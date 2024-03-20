This is the source code for bapcsbot (and bapcsbotcanada is just a duplicate of this repo with different credentials)

This was created when I was learning programming. I learned datbases halfway through, so only the alerts portion is stored in a db (mongodb). You will need to have mongodb running and create the ReminderCollection yourself

It also uses an old version of praw, likely whatever version was relevant 6 years ago, no package management. You'll also probably want to purge most of the historic files, since they have way more in them than is needed.

to run via terminal on mac (after updating credentials, registering bot with reddit, installing praw and other used packages, setting up mongodb): 

`python redditbot.py && python reminderbot.py`