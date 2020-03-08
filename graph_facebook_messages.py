from datetime import date, datetime, timedelta
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
import sys

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
    window_size_days = 31 # Window size to average # of messages over
    start_date = date(2012, 1, 1) # Starting date to graph from
    n = 20 # How many of the top people to display?

    delta = date.today() - start_date

    xs = [start_date + timedelta(days=i) for i in range(delta.days)]

    # List of tuples of the form (total number of messages, y-values corresponding to every day, their name)
    ys_and_labels = []

    for name in all_messages:
        total_messages = 0
        y_name = [0] * len(xs)

        message_counts = all_messages[name]

        for day in message_counts:
            message_delta = day - start_date
            # Add the current day to the rolling average over the window size
            for windowed_day in range(message_delta.days - int(window_size_days / 2),
                                      message_delta.days + int(window_size_days / 2) + 1):
                y_name[windowed_day] += message_counts[day] / window_size_days

            total_messages += message_counts[day]

        ys_and_labels.append((total_messages, y_name, name))

    # Display label sorted by most messages
    ys_and_labels.sort(reverse=True)

    # Sort y-values into a set of y-values for each of the top n people and "Other"
    ys = [y_and_label[1] for y_and_label in ys_and_labels[:n]]
    other_ys = [0] * len(xs)
    for y in ys[n:]:
        for i, count in enumerate(y):
            other_ys[i] += count

    labels = [y_and_label[2] for y_and_label in ys_and_labels[:n]]
    labels.append("Other")

    # Make colors prettier
    pal = sns.color_palette("hls", n + 1)
    # This is really hardcoded for 21 basically
    colors = pal[1::2] + pal[::2]

    plt.rc('xtick', labelsize=22)
    plt.rc('ytick', labelsize=22)
    plt.rc('legend', fontsize=16)
    plt.rc('axes', titlesize=26)
    plt.title("Facebook messages per person")
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
