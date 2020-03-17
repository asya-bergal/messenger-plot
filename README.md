# messenger-plot
This code generates a stacked area graph of your instant messages, showing you who you've talked with over time.

## Usage

```
pip install -r requirements.txt
python graph_messages.py <start-YYYY-MM-DD> <end-YYYY-MM-DD> "<your name>" <input-source:path>*
```
For example, I might run
```
python graph_messages.py 2018-01-01 2020-01-01 "Asya Bergal" facebook:~/Downloads/messages
```
to graph Facebook messages between 2018 and 2020.

Currently three message input sources are supported:

* `facebook`: Facebook messenger. Go
  [here](https://www.facebook.com/settings?tab=your_facebook_information), click Download Your
  Information, and download your Messages history. Unzip the resulting archive into some directory
  (e.g., `~/Downloads/messages`).
* `adium`: Logs saved by the [Adium](https://adium.im/) IM client. Assumes all logs are given in a
  single directory as XML files. I can't guarantee this is up-to-date with the latest export format.
* `hangouts`: Google Hangouts message history, downloaded from
  [Google Takeout](https://takeout.google.com/). The `Takeout` directory should be provided.

Messages from all provided sources are aggregated together into a single plot.

### Name normalization

Names for the same people may differ across platforms (e.g., Google emails, AIM screennames,
Facebook names). You can map names from all inputs to canonical forms by writing a file called
`name_normalization.json` in the root directory with a JSON object mapping each input source name to
a canonical form.

The self-name that you provide as the script input should be provided in canonical form.

### Sorting

Names are ordered in the legend (top-to-bottom) and the graph (bottom-to-top) in order of greatest
message (word count) volume within the specified time range. The order will be different depending
on the time range specified.
