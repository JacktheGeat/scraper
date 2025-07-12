from pathlib import Path
import time
import requests

user_urls = {"https://api.github.com/users/JacktheGeat":0}
repo_urls = []

def getUserData(link):
    response =  requests.get(link).json()
    print(response)
    getFollowers(response["followers_url"])
    getFollowing(response["following_url"].split("{")[0])
    getStarred(response["starred_url"].split("{")[0])
    getWatches(response["subscriptions_url"])

def getStarred(link):
    response =  requests.get(link).json()
    print(f"this user has starred {len(response)} repos")

def getWatches(link):
    response =  requests.get(link).json()
    print(f"this user is watching {len(response)} repos")

def getFollowers(link):
    response = requests.get(link).json()
    print(f"this user is being followed by {len(response)} people")
    for user in response:
        user_urls[user["url"]] = user_urls.get(user["url"], 0) + 1


def getFollowing(link):
    response = requests.get(link).json()
    print(f"this user is following {len(response)} people")
    for user in response:
        user_urls[user["url"]] = user_urls.get(user["url"], 0) + 1


counter = 0
while counter < len(user_urls):
    
    getUserData(list(user_urls.keys())[counter])
    time.sleep(3)
    counter += 1
    print(user_urls)