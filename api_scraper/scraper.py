from pathlib import Path
import time
import requests
from github import Github, Auth

token = ""
file = open("api_scraper/TOKEN.txt")
token=file.read()
auth = Auth.Token(token)
g = Github(auth=auth)

    # You can now interact with the GitHub API
user = g.get_user()
print(f"Logged in as: {user.login}")


user_urls = {"https://api.github.com/users/JacktheGeat":0}
repo_urls = {}

def getUserData(link):
    response =  requests.get(link).json()
    toreturn = {
                "user": response["login"],
                "numfollowers": getUsers(response["followers_url"]),
                "numfollowing": getUsers(response["following_url"].split("{")[0]),
                "numstarred": getRepos(response["starred_url"].split("{")[0]),
                "numwatches": getRepos(response["subscriptions_url"]),
                "numrepos": getRepos(response["repos_url"])
            }
    with open("api_scraper/users.txt", "a") as file: 
        file.write(str(toreturn))
        file.write("\n")
    

def getRepoData(link):
    response =  requests.get(link).json()
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
        file.write("\n")
    

# when the API returns a list of users
def getUsers(link):
    response = requests.get(link).json()
    for user in response:
        user_urls[user["url"]] = user_urls.get(user["url"], 0) + 1
    return len(response)


# when the API returns a list of repos
def getRepos(link):
    response = requests.get(link).json()
    for repo in response:
        repo_urls[repo["url"]] = repo_urls.get(repo["url"], 0) + 1
    return len(response)

counter = 0
open("api_scraper/users.txt", "w").close()

while counter < len(user_urls) + len(repo_urls):
    if counter < len(user_urls): getUserData(list(user_urls.keys())[counter])
    else: getRepoData(list(repo_urls.keys())[counter])
    time.sleep(3)
    counter += 1
    print(user_urls)

