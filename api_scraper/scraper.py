import requests
from datetime import datetime, timedelta
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
    response =  requests.get(link, headers=headers).json()
    name = response["login"]
    toReturn = {
                "user": name,
                "numrepos": getRepos(name, response["repos_url"]),
                "numfollowers": getUsers(name, response["followers_url"]),
                "numfollowing": getUsers(name, response["following_url"].split("{")[0]),
                "numstarred": getRepos(name, response["starred_url"].split("{")[0]),
                "numwatches": getRepos(name, response["subscriptions_url"]),
            }
    with open("api_scraper/users.txt", "a") as file: 
        file.write(str(toReturn))
        file.write(",\n")
    saveData()
    return toReturn
    

def getRepoData(link):
    response =  requests.get(link, headers=headers).json()
    name = response["full_name"]
    toReturn = {
                "name": name,
                "owner": response["owner"]["login"],
                "isFork": response["fork"],
                "stargazers": getUsers(name, response["stargazers_url"]),
                "subscribers": getUsers(name, response["subscribers_url"]),
                "contributors": getUsers(name, response["contributors_url"]),
                "issues":getIssues(name, response["issues_url"].split("{")[0])
            }
    with open("api_scraper/repos.txt", "a") as file: 
        file.write(str(toReturn))
        file.write(",\n")
    saveData()
    return toReturn
    

# when the API returns a list of users
def getUsers(owner, link):
    loop = True
    toReturn = 0
    i = 1
    while loop:
        numUsers = getUsersRecursion(owner, link, i)
        if numUsers < 10000: loop = False
        else:
            toReturn += numUsers
            i += 100
    return toReturn

    
def getUsersRecursion(owner, link, i=1):
    print(f"{link} page {i}")
    response = requests.get(f'{link}?page={i}&per_page={PAGESIZE}', headers=headers).json()
    for user in response:
        bigrams.update([f"{owner} : {user["login"]}"])
        if user["url"] not in user_urls:
            inQueue.append(f"user: {user["url"]}")
        user_urls[user["url"]] += 1
    toReturn = len(response)
    if toReturn >= PAGESIZE: 
        if i % 100 == 0:
            return toReturn
        return toReturn + getUsersRecursion(owner, link, i+1)
    return toReturn


# when the API returns a list of repos
def getRepos(owner, link):
    loop = True
    toReturn = 0
    i = 1
    while loop:
        numUsers = getReposRecursion(owner, link, i)
        if numUsers < 10000: loop = False
        else:
            toReturn += numUsers
            i += 100
    return toReturn

def getReposRecursion(owner, link, i = 1):
    print(f"{link} page {i}")
    response = requests.get(f'{link}?page={i}&per_page={PAGESIZE}', headers=headers).json()
    for repo in response:
        bigrams.update([f"{owner} : {repo["full_name"]}"])
        if repo["url"] not in repo_urls:
            inQueue.append(f"repo: {repo["url"]}")
        repo_urls[repo["url"]] += 1
    toReturn = len(response)
    if toReturn >= PAGESIZE & i % 100 != 0:
        return toReturn + getReposRecursion(owner, link, i+1)
    return toReturn

# Helper that converts datetime object into an integer
def time_to_int(dateobj: datetime):
    return datetime.timestamp(dateobj)
# Helper that converts integers into datetime objects
def int_to_time(dateint:int):
    if dateint == 0:
        return datetime(1, 1, 1, 0, 0, 0)
    UNIX_EPOCH = 719164
    dateobj = datetime.fromtimestamp(int(dateint))
    dateobj = dateobj - timedelta(days=UNIX_EPOCH)
    return dateobj

# when the API returns a list of issues
def getIssues(owner, link):
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

run(200)