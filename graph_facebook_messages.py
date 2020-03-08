import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import math
from datetime import *

window_size_days = 2048 # Window size to average # of messages over
start_date = date(2007, 1, 1) # Starting date to graph from
end_date = date.today()
num_top_people = 20 # How many of the top people to display

# how much to weigh a message based on distance
def get_weight(message_day, graph_day):
    stdev = 32
    return gaussian_pdf(message_day, stdev, graph_day)

# average over window
# def get_weight(message_day, graph_day):
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

# Returns dictionary from date to number of messages
def messages_per_day(messages):
    messages_per_day = {}

    for message in messages:
        message_date = date.fromtimestamp(message['timestamp_ms'] / 1000.0)
        if message_date in messages_per_day:
            messages_per_day[message_date] +=1
        else:
            messages_per_day[message_date] = 1

    return messages_per_day

def process_two_person_conversation(conversation_folder):
    their_name = ''
    messages = []

    dirpath, _, message_files = next(os.walk(conversation_folder))
    for message_file in [os.path.join(conversation_folder, f) for f in message_files]:
        with open(message_file) as f:
            convo = json.load(f)
            their_name = convo['title']

            messages += convo['messages']
            # This is a dumb starting message that Facebook leads with sometimes, ignore it
            if 'content' in messages[-1] and messages[-1]['content'].startswith('Say hi to your'):
                messages = messages[:-1]

    return (their_name, messages_per_day(messages))

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
                    weight = get_weight(message_delta.days, windowed_day)
                    inc = message_counts[day] * weight
                    y_name[windowed_day] += inc

            total_messages += message_counts[day]

        name_with_message_count = name + " (" + str(total_messages) + ")"
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
    labels.append("Other (" + str(total_other_messages) + ")")

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
    path = os.path.join(data_directory, 'messages', 'inbox')
    print(path)
    conversation_folders = next(os.walk(path))[1]
    all_messages = {}

    for folder in [os.path.join(path, c) for c in conversation_folders]:
        dirpath, _, message_files = next(os.walk(folder))
        if len(message_files) > 0:
            first_message_file = os.path.join(dirpath, message_files[0])
            with open(first_message_file) as f:
                convo = json.load(f)
                # Only process messages with two participants
                if len(convo['participants']) == 2:
                    their_name, messages_per_day = process_two_person_conversation(folder)
                    all_messages[their_name] = messages_per_day

    graph_messages_window(all_messages)

def main():
    data_directory = sys.argv[1]
    process_conversations(data_directory)

if __name__ == "__main__":
    main()