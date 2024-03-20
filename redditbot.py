import praw
from fuzzywuzzy import fuzz
import datetime
import os
from items import *
import prawcore.exceptions as e
import reminderhelper
import time

duplicate = False

def main():

    reddit = praw.Reddit(user_agent = "BapcsBot", client_id = "CLIENT_ID_HERE",
                         client_secret = "CLIENT_SECRET_HERE",
                         username = 'BapcsBot', password = 'PASSWORD_HERE')
    sub = reddit.subreddit("buildapcsales")
    reminder = reminderhelper.ReminderHelper()


    while True:
        try:
            for post in sub.stream.submissions():
                posts = get_posts()
                global duplicate
                duplicate = False
                title = post.title.replace("|", "-")
                title = title.replace("*", "-").replace("@", "-").replace("$$","$")
                tag = title[1:title.find("]")].upper()
                print(title)
                print(tag)

                if post.shortlink in posts:  # already seen post
                    continue
                if title[0] != "[" or "$" not in title:  # no price or tag info
                    continue
                if tag == "MOTHERBOARD":
                    tag = "MOBO"
                if tag not in tags:  # invalid tag
                    continue

                product = get_product(title)
                price = get_price(title)
                item = get_item(tag, product)

                if item == "" and (tag == "GPU" or tag == "CPU"):
                    continue

                if price != "$":
                    reminder.find_users_for_reminder(title, tag, post.shortlink, float(price[1:]), item)

                if os.path.isfile(tag + ".txt"):
                    match = get_matches(tag, item, product, post.url)

                    if match and len(match) > 1:
                        print(match)
                        print("match found")
                        print(post.shortlink)
                        reply = generate_reply(match)
                        if tag not in ("RAM", "SSD", "HDD", "OTHER", "VR", "LAPTOP", "PREBUILT"):
                            post.reply(reply)
                    if not duplicate:
                        with open(tag + ".txt", "a") as file:
                            file.write(item + "*" + "[" + product + "]" + "(" + post.shortlink + ")" +
                                       "|" + price + "|" + "@" +
                                       str(datetime.datetime.fromtimestamp(post.created)) + "|" + post.url + "\n")

                    add_post(post.shortlink)

                else:
                    with open(tag + ".txt", "w") as file:
                        pass
        except e.ResponseException as error:
            print(error)
            print("Connection issue")
            time.sleep(60)
            pass
        except e.RequestException as error:
            print(error)
            print("Connection issues2")
            time.sleep(60)


def add_post(url):
    """Adds post url to completed posts"""
    with open("CompletedPosts.txt", "a") as file:
        file.write(url + "\n")


def get_posts():
    """Gets already viewed posts from text file"""
    if not os.path.isfile("CompletedPosts.txt"):
        file = open("CompletedPosts.txt", "w")
        file.close()
    with open("CompletedPosts.txt", "r") as file:
        return file.read().splitlines()


def get_price(title):
    """Gets price from title"""
    try:
        price = ""
        i = title.find("$")
        if "=" in title and "$" in title[title.find("="):]:
            splt = title.split("=")
            i = splt[1].find("$") + len(splt[0]) + 1
        while i < len(title) and (title[i].isdigit() or title[i] in ("$", ".", ",")):
            price += title[i]
            i += 1
        if price == "$":
            global duplicate
            duplicate = True
        else:
            while not price[-1].isdigit():
                price = price[0:-1]
        price = price.replace(",","")
        return price
    except:
        return "$"


def get_item(tag, product):
    """Categorizes GPUs, RAM, and CPUs into popular models"""
    line = product.replace(" ", "").lower()
    item = ""
    if tag == "GPU":
        for gpu_item in GPU_items:
            if gpu_item in line:
                if gpu_item == "1060":
                    if "3gb" in line:
                        item = "1060 3gb"
                    elif "6gb" in line:
                        item = "1060 6gb"
                elif gpu_item == "rx580":
                    if "4gb" in line:
                        item = "rx580 4gb"
                    elif "8gb" in line:
                        item = "rx580 8gb"
                else:
                    item = gpu_item
                break

    elif tag == "RAM":
        speed = None
        size = None
        for ram_speed in RAM_speeds:
            if ram_speed in line:
                speed = ram_speed
                break
        for ram_size in RAM_sizes:
            if ram_size in line:
                size = ram_size
                break
        if speed and size:
            item = speed + " " + size

    elif tag == "CPU":
        for cpu_item in CPU_items:
            if cpu_item in line:
                item = cpu_item
                break

    elif tag == "MONITOR":
        print("MONITOR, looking for " + line)
        for monitor_item in MONITOR_items:
            if monitor_item in line:
                item = monitor_item
                break

    return item


def convert_date(line):
    """Converts date in line to x days ago"""
    print(line)
    item_date = datetime.datetime.strptime(line.split("@")[1][0:19], "%Y-%m-%d %H:%M:%S")
    days_ago = (datetime.date.today() - item_date.date()).days
    if days_ago == 0 or days_ago == -1:
        when = "today"
    elif days_ago == 1:
        when = str(days_ago) + " day ago"
    else:
        when = str(days_ago) + " days ago"
    url = line.split("@")[1][19:]
    remainder = get_vendor(url)
    return line.split("@")[0] + when + remainder


def check_dead_link(r, url):
    """Checks for deleted posts so they are not included"""
    post = r.submission(url=url)
    if post.author is None:
        return True
    else:
        return False
    
    
def get_product(title):
    """Obtains just product name from title, excluding price info and tag"""
    product = title[title.find("]") + 1:title.find("$")].strip()
    if "]" in product: # if they double tagged item
        product = product[product.find("]") + 1:]
    if "(" in product:
        product = product[0:product.find("(")]
    return product


def get_vendor(url):
    """Gets website name from url"""
    if url[1:5] == "http":
        url = url[url.find("://") + 3:]
    if url.split("/")[0].count(".") > 1:
        url = url[url.find(".") + 1:]
    url = url[0:url.find(".")]
    return "|" + url


def get_matches(tag, item, product, url):
    """Searches through previous posts to find same item or similar product title"""
    print("get_matchs: " + tag)
    match = []
    with open(tag + ".txt", "r", errors="replace") as file:
        for full_line in file:
            try:
                if url.strip() == full_line.split("|")[-1].strip(): # same exact item link
                    global duplicate
                    duplicate = True
                    continue
                elif full_line[0] != "*" and item != "" and len(full_line.split("*")) > 1:  # have item tag
                    line_item, line = full_line.split("*")
                    item_date = datetime.datetime.strptime(line.split("@")[1][0:19], "%Y-%m-%d %H:%M:%S")
                    days_ago = (datetime.date.today() - item_date.date()).days
                    if item == line_item and days_ago < 60:
                        match.append(convert_date(line))
                elif item == "":
                    line = full_line[1:]
                    item_date = datetime.datetime.strptime(line.split("@")[1][0:19], "%Y-%m-%d %H:%M:%S")
                    days_ago = (datetime.date.today() - item_date.date()).days
                    if fuzz.ratio(product, line[0:line.find("]")]) > 70 and days_ago < 60:
                        match.append(convert_date(line))
            except:
                continue

    return match


def generate_reply(match):
    """Generates table formatted reply"""
    reply = ""
    if len(match) > 5:
        match = match[-5:]
    reply += "I found similar item(s) posted recently: \n\n"
    reply += "Item | Price | When | Vendor\n"
    reply += ":-|:-:|:-:|-:\n"
    for m in match:
        reply += m
        reply += "\n"
    reply += "\n"
    reply += "I'm a bot! Please send all bugs/suggestions in a private message to me"
    reply += "\n\n"
    reply += "**Want to get alerts when certain items are posted? Try out the [alert feature!](https://pastebin.com/PJx2J2Vh)**\n\n"
    reply += "You can also send me a direct message (NOT THE CHAT BUBBLE THING) to set up item alerts"
    return reply


if __name__ == "__main__":
    main()
