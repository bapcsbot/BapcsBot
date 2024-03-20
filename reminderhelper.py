import praw
from pymongo import MongoClient
from praw.models import Redditor
from praw.exceptions import APIException
from items import *

class ReminderHelper:

    def __init__(self):
        client = MongoClient()
        db = client.Reminders
        self.col = db.ReminderCollection
        self.reddit = praw.Reddit(user_agent="BapcsBot", client_id="CLIENT_ID_HERE",
                         client_secret="CLIENT_SECRET_HERE",
                         username='BapcsBot', password='PASSWORD_HERE')

    def find_users_for_reminder(self, full_title, tag, post_url, price, post_item):
        """Find users who set reminder for specified item and tag"""
        title = full_title.lower().replace(" ", "")
        seen_usernames = {}
        reminders = self.col.find({"tag": tag})
        generic_usernames = []
        if price != "$":
            for r in reminders:
                if r["username"] in seen_usernames:
                    continue
                item = r["item"]
                item_no_white = item.lower().replace(" ", "")
                if item_no_white == "all":
                    generic_usernames.append(r["username"])
                if price > float(r["price"]):
                    continue
                if item_no_white in GPU_items or item_no_white in CPU_items or item_no_white in ("10606gb", "10603gb", "rx5808gb", "rx5804gb"):
                    if item.lower().replace(" ", "") == post_item.lower().replace(" ", "") or (item_no_white == "5800x" and post_item == "5800x3d"):
                        seen_usernames[r["username"]] = True
                        self.reply_to_user(r["username"], item, post_url, price, full_title)
                elif item_no_white == "580":
                    if "580" in title:
                        seen_usernames[r["username"]] = True
                        self.reply_to_user(r["username"], item, post_url, price, full_title)
                elif item.lower().replace(" ", "") in title:
                    seen_usernames[r["username"]] = True
                    self.reply_to_user(r["username"], item, post_url, price, full_title)
        else:
            for r in reminders:
                item = r["item"]
                if item.lower().replace(" ","") == "all":
                    generic_usernames.append(r["username"])
        if generic_usernames:
            for username in generic_usernames:
                self.generic_reply_to_user(username, tag, post_url, full_title)

    def generic_reply_to_user(self, username, tag, post_url, title):
        """sends message to user about tag found"""
        print("GENERIC MESSAGE TO " + username)
        redditor = Redditor(self.reddit, name=username)
        subject = tag + " posted"
        message = "Link to post: " + post_url + "\n\n" + title + "\n\nReply with !stop to stop receiving alerts"
        try:
            redditor.message(subject, message)
        except APIException:
            print(username)
            return

    def reply_to_user(self, username, item, post_url, price, title):
        """Send message to user"""
        print("MESSAGE SENT TO " + username + " about " + item + ": " + post_url)
        redditor = Redditor(self.reddit, name=username)
        subject = item + " found for " + str(price)
        message = "Link to post: " + post_url + "\n\n" + title + "\n\nReply with !stop to stop receiving alerts"
        try:
            redditor.message(subject, message)
        except APIException:
            print(username)
            return
