import requests
from datetime import datetime
from collections import Counter

file = open("api_scraper/TOKEN.txt")
token=file.read()
file.close()
headers = {'Authorization': 'token ' + token}

login = requests.get('https://api.github.com/user', headers=headers)

CURRENTTIME = datetime.now()
PAGESIZE = 100

with open("api_scraper/repos.txt", "a") as reposFile: 
    reposFile.write("[")
with open("api_scraper/users.txt", "a") as usersFile: 
    usersFile.write("[")


user_urls = Counter({"https://api.github.com/users/JacktheGeat":0})
repo_urls = Counter()
inQueue = ["user: https://api.github.com/users/JacktheGeat"]
bigrams = Counter()

def getUserData(link):
    '''
    Gets data about a user, adding any connections to the bigram counter and queue.

    Args:
        link (str): A Github API link for a user
    
    Returns:
        userData (dict):
            >>> "user" (str): Name of repository
            "repos" (int): Number of repos
            "followers" (int): Number of people following the user
            "following" (int): Number of pwople the user is following
            "gists" (int): Number of gists
            "starred" (int): Number of repos the user has starred
            "watching" (int): Number of repos the user is watching
    '''
    response =  requests.get(link, headers=headers).json()
    name = response["login"]
    getRepos(response["repos_url"], name)
    getUsers(response["following_url"].split("{")[0], name)
    toReturn = {
                "user": name,
                "repos": response["public_repos"],
                "followers": response["followers"],
                "following": response["following"],
                "gists": response["public_gists"],
                "starred": getRepos(response["starred_url"].split("{")[0], name),
                "watching": getRepos(response["subscriptions_url"], name),
            }
    with open("api_scraper/users.txt", "a") as file: 
        file.write(str(toReturn))
        file.write(",\n")
    saveData()
    return toReturn
    

def getRepoData(link):
    '''
    Gets data about a repository, adding any connections to the bigram counter and queue.

    Args:
        link (str): A Github API link for a repository
    
    Returns:
        userData (dict):
            >>> "name" (str): Name of repository
            "owner" (str): Owner of the repository
            "isFork" (bool): Is repository a fork
            "stargazers" (int): Number of users who have starred the repository
            "watchers" (int): Number of users who are watching the repository
            "contributors" (int): Number of users who have contributed to the repository
            "issues" (dict): Various data on repository issues
    '''
    response =  requests.get(link, headers=headers).json()
    name = response["full_name"]
    getUsers(response["subscribers_url"],name)
    getUsers(response["stargazers_url"],name)
    toReturn = {
                "name": name,
                "owner": response["owner"]["login"],
                "isFork": response["fork"],
                "stargazers": response["stargazers_count"],
                "watchers": response["watchers_count"],
                "contributors": getUsers(response["contributors_url"],name),
                "issues":getIssues(response["issues_url"].split("{")[0],name)
            }
    if toReturn["isFork"]: 
        toReturn["parent"] = {"name": response["parent"]["full_name"]}
        # Add parent to queue
    with open("api_scraper/repos.txt", "a") as file: 
        file.write(str(toReturn))
        file.write(",\n")
    saveData()
    return toReturn
    

# when the API returns a list of users
def getUsers(link: str, owner:str=None):
    '''
    Adds a list of users to the queue.
    If the owner is set, also adds "owner : <user>" to bigrams counter
    Args:
        link (str): A Github API link for a list of users
        owner (str) : The "owner" of the list, or who the bigram is originating from.
    
    Returns:
        numUsers (int): The number of users in the list.
    '''
    print(f"{link}")
    response = requests.get(f'{link}?per_page=100', headers=headers)
    data = response.json()
    toReturn = 0
    for user in data:
        toReturn +=1
        if owner != None: bigrams.update([f"{owner} : {user["full_name"]}"])
        if user["url"] not in user_urls: inQueue.append(f"user: {user["url"]}")
        user_urls[user["url"]] += 1

    counter = 1
    while 'next' in response.link:
        counter += 1
        print(f"{link} page {counter}")
        response = requests.get(response.links['next']['url'], headers=headers)
        data = response.json()
        for user in data:
            toReturn +=1
            if owner != None: bigrams.update([f"{owner} : {user["full_name"]}"])
            if user["url"] not in user_urls: inQueue.append(f"user: {user["url"]}")
            user_urls[user["url"]] += 1
    return toReturn


# when the API returns a list of repos
def getRepos(link: str, owner:str=None):
    '''
    Adds a list of repositories to the queue.
    If owner is set, also adds "owner : <repo>" to bigrams counter
    Args:
        link (str): A Github API link for a list of repositories
        owner (str) : The "owner" of the list, or who the bigram is originating from.
    
    Returns:
        numRepos (int): The number of repositories in the list.
    '''
    print(f"{link}")
    response = requests.get(f'{link}?per_page=100', headers=headers)
    data = response.json()
    toReturn = 0
    for repo in response:
        toReturn +=1
        if owner != None: bigrams.update([f"{owner} : {repo["full_name"]}"])
        if repo["url"] not in repo_urls: inQueue.append(f"repo: {repo["url"]}")
        repo_urls[repo["url"]] += 1

    counter = 1
    while 'next' in response.link:
        counter += 1
        print(f"{link} page {counter}")

        response = requests.get(response.links['next']['url'], headers=headers)
        data = response.json()
        for repo in response:
            toReturn += 1
            if owner != None: bigrams.update([f"{owner} : {repo["full_name"]}"])
            if repo["url"] not in repo_urls: inQueue.append(f"repo: {repo["url"]}")
            repo_urls[repo["url"]] += 1
    return toReturn

# when the API returns a list of issues
def getIssues(link, owner):
    '''
    Gets data about a repository, adding any connections to the bigram counter and queue.

    Args:
        link (str): A Github API link for a liar of issues
    
    Returns:
        issueData (dict):
            >>> "numIssues" (int): total number of issues
            "active" (int): number of active issues
            "closed" (int): number of closed issues,
            "avg_close_time" (int): a timestamp representing the average time it takes to close an issue.
    '''
    response =  requests.get(link, headers=headers).json()
    avgCloseTime = []
    numClosed = 0
    for issue in response:
        if issue["state"] == "closed": numClosed += 1
        created = time_to_int(datetime.fromisoformat(issue["created_at"]).replace(tzinfo=None))
        closed = time_to_int(datetime.fromisoformat(issue["closed_at"]) if issue["closed_at"] != None else CURRENTTIME)
        avgCloseTime.append(closed - created)
    
    avgCloseTime = sum(avgCloseTime)/len(avgCloseTime) if len(avgCloseTime) != 0 else 0
    toReturn = {
        "numIssues": len(response),
        "active": len(response)-numClosed,
        "closed": numClosed,
        "avg_close_time": int(avgCloseTime)
    }
    return toReturn

def saveData():
    '''
    Helper function that saves the different lists in case of a crash.
        * queue
        * bigrams
        * seenUsers
        * seenRepos
    '''
    with open("api_scraper/queue.txt", "w") as file: 
        file.write(str(inQueue))
    with open("api_scraper/bigrams.txt", "w") as file: 
        file.write(str(bigrams))
    with open("api_scraper/seenUsers.txt", "w") as file: 
        file.write(str(user_urls))
    with open("api_scraper/seenRepos.txt", "w") as file: 
        file.write(str(repo_urls))
    

def run(iterations):
    open("api_scraper/users.txt", "w").close()
    open("api_scraper/repos.txt", "w").close()

    while inQueue and iterations > 0:
        if inQueue[0][:6] == "user: ":
            getUserData(inQueue[0][6:])
        else:
            getRepoData(inQueue[0][6:])
        inQueue.pop(0)
        iterations -= 1

    print(f"num users seen: \t\t{len(user_urls.items())}")
    print(f"num repos seen: \t\t{len(repo_urls.items())}")
    print(f"total remaining  in queue: \t{len(inQueue)}")

run(50)