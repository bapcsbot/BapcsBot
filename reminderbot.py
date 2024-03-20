import praw
from pymongo import MongoClient
from praw.models import Comment
from praw.models import Redditor
from items import *
from requests.packages.urllib3.exceptions import ReadTimeoutError
import time
import collections
import sys


class ReminderBot:

    def __init__(self):
        client = MongoClient()
        db = client.Reminders
        self.col = db.ReminderCollection
        self.reddit = praw.Reddit(user_agent="BapcsBot", client_id="CLIENT_ID_HERE",
                         client_secret="CLIENT_SECRET_HERE",
                         username='BapcsBot', password='PASSWORD_HERE')
        self.inbox = self.reddit.inbox
        self.start()

    def start(self):
        """Start bot"""
        while True:
            try:
                for mail in self.inbox.stream():
                    mail.mark_read()
                    self.process_comment(mail.body, mail.author)
                    message = mail.body.lower().replace("> ", "")
                    if message.startswith("!stop"):
                        item = ""
                        if len(message.strip().split(" ")) > 1:
                            item = message[6:]
                        self.remove_user(mail.author, item)
                    elif message == "!help" or message == "help":
                        mail.author.message("Bapcsbot Help", "https://pastebin.com/1fAc4iKi")
                    elif message == "!list":
                        self.list_items(mail.author)
            except Exception as err:
                print(err)
                print("Connection issue")
                e = sys.exc_info()[0]
                print(e)
                time.sleep(60)
                pass

    def process_generic(self, user, tag):
        """Process tag alert"""
        dct = {"tag": tag,
               "item": "ALL",
               "username": user.name,
               "price": "9999.00"}
        self.col.insert_one(dct)
        print("MESSAGE SENT")
        message = "Hi, you're now set up to receive an alert if a " + tag + " is posted \
                  \n\n reply with !stop to stop all alerts, !list to show all current alert subscriptions"
        user.message("Bapcsbot Alert Confirmation", message)


    def process_comment(self, text, user):
        """Process comment text"""
        textFull = text.strip()
        for text in textFull.split("\n"):
            print(user.name + ": " + text)
            if text[0:6].lower() != "!alert":
                print("Not an alert")
                return
            text = text[7:]
            split_text = text.split(",")
            if len(split_text) == 4:
                split_text = split_text[1:]
                print(split_text)
            tag = split_text[0].strip().replace("[", "").replace("]", "").upper()
            if len(split_text) == 1 and tag in tags:
                self.process_generic(user, tag)
                return
            if len(split_text) != 3:
                print("Wrong format")
                return

            item = split_text[1].strip()
            try:
                price = "{:.2f}".format(float(split_text[2].strip().replace("$","")))
            except ValueError:
                print("Invalid price: " + split_text[2].strip())
                return
            if tag not in tags:
                print("Invalid tag: " + tag)
                return
            if item == "":
                print("No item: " + item)
                return

            item_formatted = item.replace(" ", "").lower()
            if tag == "GPU":
                if item_formatted == "1060" or item_formatted == "10606gb" or item_formatted == "gtx1060":
                    item = "10606gb"
                elif item_formatted == "rx580" or item_formatted == "rx5808gb" or item_formatted == "580":
                    item = "rx5808gb"
                elif item_formatted == "590":
                    item = "rx590"
                elif item_formatted == "10603gb" or item_formatted == "rx5804gb":
                    item = item_formatted
                else:
                    print("item before: " + item)
                    for i in GPU_items:
                        if i in item_formatted:
                            item = i
                            break
            elif tag == "CPU":
                print("item before: " + item)
                print(CPU_items)
                for i in CPU_items:
                    if i in item_formatted:
                        item = i
                        break
            print("item after: " + item)

            dct = {"tag": tag,
                    "item": item,
                    "username": user.name,
                    "price": price}
            self.col.insert_one(dct)
            print("MESSAGE SENT")
            message = "Hi, you're now set up to receive an alert if a(n) " + item + " " + tag +\
                      " goes on sale for less than $" + price + "\n\n reply with !stop to stop all alerts, !list to show all current alert subscriptions"
            user.message("Bapcsbot Alert Confirmation", message)

    def remove_user(self, user, item=""):
        """Remove user from database"""
        reminders = self.col.find({"username": user.name})
        message_title = "Unsubscribe failed"
        if item:
            message_body = "I couldn't find any existing alerts for " + item
        else:
            message_body = "Already unsubscribed!"
        for r in reminders:
            if item:
                if r["item"].lower().replace(" ", "") == item.lower().replace(" ", "") or (item.lower().replace(" ", "") == r["tag"].lower().replace(" ","") and r["item"] == "ALL"):
                    self.col.delete_one(r)
                    message_title = "Unsubscribed from " + item + " alerts"
                    message_body = "You've been unsubscribed from Bapcs alerts for " + item

            else:
                message_title = "Unsubscribed from Bapcs Alerts"
                message_body = "You've been unsubscribed from all Bapcs alerts"
                self.col.delete_one(r)
        user.message(message_title, message_body)

    def list_items(self, user):
        """lists all items for a specific user"""
        reminders = self.col.find({"username": user.name})
        reply = "Here are your currently subscribed alerts:\n\n"
        reply += "Tag | Item | Price\n"
        reply += ":-|:-:|:-\n"
        for r in reminders:
            tag = r["tag"]
            item = r["item"]
            price = r["price"]
            reply += (tag + "|" + item + "|" + price + "\n")
        reply += "\n\nTo stop a single item alert, reply with !stop itemname. \nTo stop all alerts, reply with !stop"
        user.message("Bapcsbot alerts list", reply)

def main():
    bot = ReminderBot()

if __name__ == "__main__":
    main()
