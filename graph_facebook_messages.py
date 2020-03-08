import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import math
from datetime import *

user_name = 'Asya Bergal'
window_size_days = 512 # Window size to average # of messages over
window_smoothing_width_days = 32 # stdev of gaussian to convolve over the data
start_date = date(2007, 1, 1) # Starting date to graph from
end_date = date.today()
num_top_people = 20 # How many of the top people to display

# for word count
def get_message_weight(msg):
    if 'content' in msg:
        return len(msg['content'].split(' '))
    else:
        return 1

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

# returns a list of (timestamp, participants, weight) tuples, where participants equally share message weight
def process_conversation(convo):
    participants = set([p['name'] for p in convo['participants']])
    if user_name in participants:
        participants.remove(user_name)
    if len(participants) == 0:
        return []

    messages = convo['messages']
    # This is a dumb starting message that Facebook leads with sometimes, ignore it
    if 'content' in messages[-1] and messages[-1]['content'].startswith('Say hi to your'):
        messages = messages[:-1]

    def get_local_participants(msg):
        sender = msg['sender_name']
        if sender == user_name:
            return participants
        else:
            return set([sender])

    return [(msg['timestamp_ms'] / 1000.0, get_local_participants(msg), get_message_weight(msg)) for msg in messages]

def graph_messages_window(all_messages):

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

            total_messages += message_counts[day]

        name_with_message_count = name + " (" + str(int(total_messages)) + ")"
        ys_and_labels.append((total_messages, y_name, name_with_message_count))

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

    labels = [y_and_label[2] for y_and_label in ys_and_labels[:num_top_people]]
    labels.append("Other (" + str(int(total_other_messages)) + ")")

    # Make colors prettier
    pal = sns.color_palette("hls", num_top_people)
    # This is really hardcoded for 20 basically
    colors = spread_list(pal, 4)
    other_color = (0.9, 0.9, 0.9) #Grey
    colors.append(other_color)

    plt.rc('xtick', labelsize=22)
    plt.rc('ytick', labelsize=22)
    plt.rc('legend', fontsize=8)
    plt.rc('axes', titlesize=26)
    plt.title("Facebook messages by person")
    plt.stackplot(xs, *ys, other_ys, colors=colors, labels=labels)
    plt.legend(loc='upper left')
    plt.show()

def process_conversations(data_directory):
    inbox = os.path.join(data_directory, 'messages', 'inbox')
    # all_messages: list of (time_seconds, creditors)
    all_messages = []
    for thread_dir in [os.path.join(inbox, c) for c in os.listdir(inbox)]:
        for msg_file in [os.path.join(thread_dir, c) for c in os.listdir(thread_dir)]:
            if msg_file.endswith(".json"):
                with open(msg_file) as f:
                    convo = json.load(f)
                    all_messages.extend(process_conversation(convo))

    all_people = set.union(*[ps for _, ps, _ in all_messages])

    messages_by_day_by_person = {}
    for person in all_people:
        messages_per_day = {}
        for time_seconds, creditors, weight in all_messages:
            if person in creditors:
                num_creditors = len(creditors)
                message_date = date.fromtimestamp(time_seconds)
                if message_date in messages_per_day:
                    messages_per_day[message_date] += 1.0 * weight / num_creditors
                else:
                    messages_per_day[message_date] =  1.0 * weight / num_creditors

        messages_by_day_by_person[person] = messages_per_day

    graph_messages_window(messages_by_day_by_person)

def main():
    data_directory = sys.argv[1]
    process_conversations(data_directory)

if __name__ == "__main__":
    main()