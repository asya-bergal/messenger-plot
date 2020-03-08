# messenger-plot
This code generates a stacked area graph of your Facebook messages, showing you who you've talked with over time.

First, go [here](https://www.facebook.com/settings?tab=your_facebook_information) -> Download Your Information and download your Messages history. Unzip the resulting archive into some directory.

Then, clone this repo and run:
```
pip install -r requirements.txt
python graph_facebook_messages.py <directory with messages> <Facebookfirstname Facebooklastname> <start date as YYYY-MM-DD>
```
