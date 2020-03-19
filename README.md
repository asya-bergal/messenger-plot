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
* `gtalk`: Google Talk chat logs from before the days of Hangouts. These must be downloaded through
  IMAP. We assume the format produced by the script [here](https://github.com/coandco/gtalk_export).
* `iphone`: Message (i.e., SMS and iMessage) logs from an iPhone backup. These will need to be
  preprocessed as described [below](#preprocessing-iphone-backups).

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

### Preprocessing iPhone Backups

You will need to back up your iPhone unencrypted. Then you will find two sqlite database files in
the backup, with the following names:

* Contacts: `31bb7ba8914766d4ba40d6dfb6113c8b614be442`
* Messages: `3d0d7e5fb2ce288813306e4d4636395e047a3d28`

In the directory you will provide to `graph_messages.py` after `iphone:`, you should run the
following.

For contacts:
```
sqlite3 /path/to/iphone/backup/31bb7ba8914766d4ba40d6dfb6113c8b614be442
> .mode csv
> .output contacts.csv
> select ABMultiValue.value
       , (select first from ABPerson where ROWID = ABMultiValue.record_id)
       , (select last from ABPerson where ROWID = ABMultiValue.record_id)
from ABMultiValue
where property = 3 or property = 4;
```

For messages:
```
sqlite3 /path/to/iphone/backup/3d0d7e5fb2ce288813306e4d4636395e047a3d28
> .mode csv
> .output messages.csv
> select datetime(message.date / 1000000000, 'unixepoch', '+31 years', '-6 hours') as Timestamp, handle.id, message.text,
    case when message.is_from_me then 'sent' else 'received' end as Sender
from message, handle where message.handle_id = handle.ROWID;
```
Here you may need to remove the division by 10^9, depending on how old the backup is. Double-check
the times in the resulting CSV to make sure they appear and they're reasonable.

