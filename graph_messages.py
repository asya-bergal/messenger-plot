import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import math
from datetime import *

window_smoothing_width_days = 50 # stdev of gaussian to convolve over the data
window_size_days = 8 * window_smoothing_width_days # Window size to average # of messages over
num_top_people = 15 # How many of the top people to display
color_spread_skip = num_top_people // 5 # stride over color
enable_group_chats = True
anonymize = False

# for word count
def get_message_weight(text_contents):
    return len(text_contents.split(' '))

# for just per-message
# def get_message_weight(msg):
#     return 1

# how much to weigh a message based on distance
# use a gaussian for smoothing
def get_weight_for_time(message_day, graph_day):
    stdev = window_smoothing_width_days
    return gaussian_pdf(message_day, stdev, graph_day)

# average over window
# def get_weight_for_time(message_day, graph_day):
#     return 1.0 / window_size_days

def gaussian_pdf(mean, stdev, x):
    variance = stdev ** 2
    offset = abs(mean - x)
    return math.exp(-(offset ** 2)/(2 * variance)) / math.sqrt(2 * math.pi * variance)

def spread_list(items, k):
    res = []
    for i in range(0, k):
        res = res + items[i::k]
    return res

if anonymize:
    anon_names = []
    with open('anon_names.txt') as f:
        anon_names = [name.strip() for name in f.readlines()]

name_norm_filename = 'name_normalization.json'
name_normalization = {}
if os.path.exists(name_norm_filename) and os.path.isfile(name_norm_filename):
    with open(name_norm_filename) as f:
        name_normalization = json.load(f)

def normalize_name(name):
    if name in name_normalization:
        return name_normalization[name]
    else:
        return name

def graph_messages_window(all_messages, start_date, end_date):

    delta = end_date - start_date

    xs = [start_date + timedelta(days=i) for i in range(delta.days)]

    # List of tuples of the form (total number of messages, y-values corresponding to every day, their name)
    ys_and_labels = []

    for name in all_messages:
        total_messages = 0
        y_name = [0] * len(xs)

        message_counts = all_messages[name]

        for day in message_counts:
            message_delta = day - start_date
            for windowed_day in range(message_delta.days - int(window_size_days / 2),
                                      message_delta.days + int(window_size_days / 2) + 1):
                if windowed_day > 0 and windowed_day < len(y_name):
                    weight = get_weight_for_time(message_delta.days, windowed_day)
                    inc = message_counts[day] * weight
                    y_name[windowed_day] += inc

            if message_delta.days > 0 and message_delta.days < len(y_name):
                total_messages += message_counts[day]

        ys_and_labels.append((total_messages, y_name, name, total_messages))

    # Display label sorted by most messages
    ys_and_labels.sort(reverse=True)

    # Sort y-values into a set of y-values for each of the top n people and "Other"
    ys = [y_and_label[1] for y_and_label in ys_and_labels[:num_top_people]]
    other_ys = [0] * len(xs)
    total_other_messages = 0
    for y_and_label in ys_and_labels[num_top_people:]:
        y = y_and_label[1]
        for i, count in enumerate(y):
            other_ys[i] += count
        total_other_messages += y_and_label[0]

    top_ys_and_labels = ys_and_labels[:num_top_people]

    anon_mapping = { name: name for _, _, name, _ in top_ys_and_labels }
    if anonymize:
        anon_mapping = { name: anon_names[i] for i, (_, _, name, _) in enumerate(top_ys_and_labels) }

    labels = ["%s (%d)" % (anon_mapping[y_and_label[2]], int(y_and_label[3])) for y_and_label in top_ys_and_labels]
    labels.append("Other (%d)" % int(total_other_messages))

    # Make colors prettier
    pal = sns.color_palette("hls", num_top_people)
    # This is really hardcoded for 20 basically
    colors = spread_list(pal, color_spread_skip)
    other_color = (0.9, 0.9, 0.9) #Grey
    colors.append(other_color)

    plt.rc('xtick', labelsize=16)
    plt.rc('ytick', labelsize=16)
    plt.rc('legend', fontsize=8)
    plt.rc('axes', titlesize=24)
    plt.title("Message word count by person over time")
    plt.stackplot(xs, *ys, other_ys, colors=colors, labels=labels, baseline='wiggle')
    plt.legend(loc='upper right')
    plt.show()

def aggregate_messages(
        messages_by_day_by_person,
        all_messages):

    all_people = set.union(*[ps for _, ps, _ in all_messages])

    for person in all_people:
        if person in messages_by_day_by_person:
            messages_per_day = messages_by_day_by_person[person]
        else:
            messages_per_day = {}
            messages_by_day_by_person[person] = messages_per_day
        for message_date, creditors, weight in all_messages:
            if person in creditors:
                num_creditors = len(creditors)
                if message_date in messages_per_day:
                    messages_per_day[message_date] += 1.0 * weight / num_creditors
                else:
                    messages_per_day[message_date] =  1.0 * weight / num_creditors


# returns a list of (timestamp, participants, weight) tuples, where participants equally share message weight
def process_adium_conversation(convo):
    namespaces = { 'default': "http://purl.org/net/ulf/ns/0.4-02" }
    user_name = convo.get('account')
    messages = [x for x in convo.findall('default:message', namespaces = namespaces)]
    participants = set([normalize_name(p.get('sender')) for p in messages])
    if user_name in participants:
        participants.remove(user_name)
    if len(participants) == 0:
        return []
    if len(participants) != 1 and not enable_group_chats:
        return []

    def get_local_participants(msg):
        sender = normalize_name(msg.get('sender'))
        if sender == user_name:
            return participants
        else:
            return set([sender])

    return [(
        datetime.fromisoformat(msg.get('time')).date(),
        get_local_participants(msg),
        get_message_weight(ET.tostring(msg, method='text').decode())
    ) for msg in messages]

import xml.etree.ElementTree as ET

def get_all_adium_messages(
        data_directory,
        user_name,
        start_date):
    # all_messages: list of (time_seconds, creditors)
    all_messages = []
    for msg_file in [os.path.join(data_directory, c) for c in os.listdir(data_directory)]:
        if msg_file.endswith(".xml"):
            convo = ET.parse(msg_file).getroot()
            all_messages.extend(process_adium_conversation(convo))

    return all_messages

# returns a list of (timestamp, participants, weight) tuples, where participants equally share message weight
def process_facebook_conversation(convo, user_name):
    participants = set([normalize_name(p['name']) for p in convo['participants']])
    if user_name in participants:
        participants.remove(user_name)
    if len(participants) == 0:
        return []
    if len(participants) != 1 and not enable_group_chats:
        return []

    messages = convo['messages']
    # This is a dumb starting message that Facebook leads with sometimes, ignore it
    if 'content' in messages[-1] and messages[-1]['content'].startswith('Say hi to your'):
        messages = messages[:-1]

    def get_local_participants(msg):
        sender = normalize_name(msg['sender_name'])
        if sender == user_name:
            return participants
        else:
            return set([sender])

    return [(
        date.fromtimestamp(msg['timestamp_ms'] / 1000.0),
        get_local_participants(msg),
        get_message_weight(msg.get('content') or '')
    ) for msg in messages]

def get_all_facebook_messages(
        data_directory,
        user_name,
        start_date):
    inbox = os.path.join(data_directory, 'messages', 'inbox')
    all_messages = []
    for thread_dir in [os.path.join(inbox, c) for c in os.listdir(inbox)]:
        for msg_file in [os.path.join(thread_dir, c) for c in os.listdir(thread_dir)]:
            if msg_file.endswith(".json"):
                with open(msg_file) as f:
                    convo = json.load(f)
                    all_messages.extend(process_facebook_conversation(convo, user_name))

    return all_messages

# returns a list of (timestamp, participants, weight) tuples, where participants equally share message weight
def process_hangouts_conversation(convo, user_name):
    participant_id_to_name = {
        p['id']['chat_id']: normalize_name(p.get('fallback_name') or p['id']['chat_id'])
        for p in convo['conversation']['conversation']['participant_data']
    }
    participants = set([name for _, name in participant_id_to_name.items()])
    if user_name in participants:
        participants.remove(user_name)
    if len(participants) == 0:
        return []
    if len(participants) != 1 and not enable_group_chats:
        return []

    messages = []
    for event in convo['events']:
        if event['event_type'] == 'REGULAR_CHAT_MESSAGE':
            sender = participant_id_to_name[event['sender_id']['chat_id']]
            if sender == user_name:
                creditors = participants
            else:
                creditors = set([sender])
            message_content = event['chat_message']['message_content']
            if 'segment' in message_content:
                message_text =  " ".join([
                    segment['text']
                    for segment in message_content['segment']
                    if segment['type'] == 'TEXT'
                ])

                messages.append((
                    date.fromtimestamp(int(event['timestamp']) // 1000000),
                    creditors,
                    get_message_weight(message_text)
                ))

    return messages

def get_all_hangouts_messages(
        data_directory,
        user_name,
        start_date):
    hangouts_file = os.path.join(data_directory, 'Hangouts', 'Hangouts.json')
    # all_messages: list of (time_seconds, creditors)
    with open(hangouts_file) as f:
        conversations = json.load(f)['conversations']

    all_messages = []
    for convo in conversations:
        all_messages.extend(process_hangouts_conversation(convo, user_name))

    return all_messages

def main():
    start_date_str = sys.argv[1]
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date_str = sys.argv[2]
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    user_name = sys.argv[3]
    messages_by_day_by_person = {}
    for arg in sys.argv[4:]:
        format_spec, data_dir = arg.split(':')
        data_dir = os.path.expanduser(data_dir)
        if format_spec == 'facebook':
            all_messages = get_all_facebook_messages(data_dir, user_name, start_date)
        elif format_spec == 'adium':
            all_messages = get_all_adium_messages(data_dir, user_name, start_date)
        elif format_spec == 'hangouts':
            all_messages = get_all_hangouts_messages(data_dir, user_name, start_date)
        aggregate_messages(messages_by_day_by_person, all_messages)

    graph_messages_window(messages_by_day_by_person, start_date, end_date)

if __name__ == "__main__":
    main()
