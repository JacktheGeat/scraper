from pathlib import Path
import time
import requests
import queue


file = open("api_scraper/TOKEN.txt")
token=file.read()
file.close()
headers = {'Authorization': 'token ' + token}

login = requests.get('https://api.github.com/user', headers=headers)

with open("api_scraper/repos.txt", "a") as reposFile: 
    reposFile.write("[")
with open("api_scraper/users.txt", "a") as usersFile: 
    usersFile.write("[")


user_urls = {"https://api.github.com/users/JacktheGeat":0}
repo_urls = {}
inQueue = ["user: https://api.github.com/users/JacktheGeat"]

def getUserData(link):
    response =  requests.get(link, headers=headers).json()
    toreturn = {
                "user": response["login"],
                "numrepos": getRepos(response["repos_url"]),
                "numfollowers": getUsers(response["followers_url"]),
                "numfollowing": getUsers(response["following_url"].split("{")[0]),
                "numstarred": getRepos(response["starred_url"].split("{")[0]),
                "numwatches": getRepos(response["subscriptions_url"]),
            }
    with open("api_scraper/users.txt", "a") as file: 
        file.write(str(toreturn))
        file.write(",\n")
    

def getRepoData(link):
    response =  requests.get(link, headers=headers).json()
    toreturn = {
                "name": response["name"],
                "owner": response["owner"]["login"],
                "isFork": response["fork"],
                "stargazers": getUsers(response["stargazers_url"]),
                "subscribers": getUsers(response["subscribers_url"]),
                "contributors": getUsers(response["contributors_url"]),
            }
    with open("api_scraper/repos.txt", "a") as file: 
        file.write(str(toreturn))
        file.write(",\n")
    

# when the API returns a list of users
def getUsers(link):
    response = requests.get(link, headers=headers).json()
    for user in response:
        if user["url"] not in user_urls:
            inQueue.append(f"user: {user["url"]}")
        user_urls[user["url"]] = user_urls.get(user["url"], 0) + 1
    return len(response)


# when the API returns a list of repos
def getRepos(link):
    response = requests.get(link, headers=headers).json()
    for repo in response:
        if repo["url"] not in repo_urls:
            inQueue.append(f"repo: {repo["url"]}")
        repo_urls[repo["url"]] = repo_urls.get(repo["url"], 0) + 1
    return len(response)

counter = 50
open("api_scraper/users.json", "w").close()
open("api_scraper/repos.json", "w").close()

while inQueue and counter > 0:
    if inQueue[0][:6] == "user: ":
        getUserData(inQueue[0][6:])
    else:
        getRepoData(inQueue[0][6:])
    inQueue.pop(0)
    counter -= 1

print(f"users: {user_urls.items()}")
print(f"repos: {repo_urls.items()}")