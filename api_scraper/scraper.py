import requests, csv, pickle, os
from datetime import datetime
from collections import Counter

file = open("api_scraper/TOKEN.txt")
token=file.read()
file.close()
headers = {'Authorization': 'token ' + token}

login = requests.get('https://api.github.com/user', headers=headers)

CURRENTTIME = datetime.now()
PAGESIZE = 100

# sets the headers
with open("api_scraper/users.csv", "a", newline='') as file: 
    writer = csv.writer(file, delimiter='|')
    fields = ["name", 
              "numrepos", 
              "numfollowers",
              "numfollowing",
              "numgists",
              "numstarred",
              "numwatching",
             ]
    writer.writerow(fields)
with open("api_scraper/repos.csv", "a", newline='') as file: 
    writer = csv.writer(file, delimiter="|")
    fields = ["name", 
              "owner", 
              "numstargazers", 
              "numwatchers", 
              "numcontributors",
              "numissues", 
              "openissues",
              "closedissues",
              "avgclosetime",
              "isFork", 
              "forkedFrom"
             ]
    writer.writerow(fields)

savedData = [[["user","https://api.github.com/users/JacktheGeat"]],Counter(), Counter(), Counter(), 0, 0, 0, 0]

# pickleIn = open(f"api_scraper/savedRun.pickle", "rb")
# savedData = pickle.load(pickleIn) # [inQueue,bigrams,repo_urls, user_urls, usersFiles,reposFiles, queueFiles, currentQueue]
# pickleIn.close()
inQueue = savedData[0]
bigrams = savedData[1]
repo_urls = savedData[2]
user_urls = savedData[3]
usersFiles = savedData[4]
reposFiles = savedData[5]
queueFiles = savedData[6]
currentQueue = savedData[7]
for i in savedData: print(i)

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
    toReturn = [name, 
                response["public_repos"],
                response["followers"],
                response["following"],
                response["public_gists"],
                getRepos(response["starred_url"].split("{")[0], name),
                getRepos(response["subscriptions_url"], name)
    ]
    with open("api_scraper/users.csv", "a", newline='') as file: 
        writer = csv.writer(file, delimiter='|')
        writer.writerow(toReturn)
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
    issuesData = getIssues(response["issues_url"].split("{")[0],name)
    toReturn = [name,
                response["owner"]["login"],
                response["stargazers_count"],
                response["watchers_count"],
                getUsers(response["contributors_url"],name),
                issuesData['numIssues'],
                issuesData['active'],
                issuesData['closed'],
                issuesData['avg_close_time'],
                response["fork"]
            ]
    if toReturn[9]: 
        toReturn.append(response["parent"]["full_name"])
        # Add parent to queue
    else: toReturn.append('')
    with open("api_scraper/repos.csv", "a", newline='') as file: 
        writer = csv.writer(file, delimiter='|')
        writer.writerow(toReturn)
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
    if response.status_code == 204 or response.status_code == 500: return 0
    data = response.json()
    toReturn = 0
    for user in data:
        toReturn +=1
        if owner != None: bigrams.update([f"{owner} : {user["login"]}"])
        addQueue('user', user["url"])
        user_urls[user["url"]] += 1

    counter = 1
    while 'next' in response.links:
        counter += 1
        print(f"{link} page {counter}")
        response = requests.get(response.links['next']['url'], headers=headers)
        if response.status_code == 204 or response.status_code == 500: return 0
        data = response.json()
        for user in data:
            toReturn +=1
            if owner != None: bigrams.update([f"{owner} : {user["login"]}"])
            addQueue('user', user["url"])
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
    if response.status_code == 204 or response.status_code == 500: return 0

    data = response.json()
    toReturn = 0
    for repo in data:
        toReturn +=1
        if owner != None: bigrams.update([f"{owner} : {repo["full_name"]}"])
        addQueue('repo', repo['url'])
        repo_urls[repo["url"]] += 1

    counter = 1
    while 'next' in response.links:
        counter += 1
        print(f"{link} page {counter}")

        response = requests.get(response.links['next']['url'], headers=headers)
        if response.status_code == 204 or response.status_code == 500: return 0

        data = response.json()
        for repo in data:
            toReturn += 1
            if owner != None: bigrams.update([f"{owner} : {repo["full_name"]}"])
            addQueue('repo', repo['url'])
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
        created = datetime.timestamp(datetime.fromisoformat(issue["created_at"]).replace(tzinfo=None))
        closed = datetime.timestamp(datetime.fromisoformat(issue["closed_at"]) if issue["closed_at"] != None else CURRENTTIME)
        avgCloseTime.append(closed - created)
    
    avgCloseTime = sum(avgCloseTime)/len(avgCloseTime) if len(avgCloseTime) != 0 else 0
    toReturn = {
        "numIssues": len(response),
        "active": len(response)-numClosed,
        "closed": numClosed,
        "avg_close_time": int(avgCloseTime)
    }
    return toReturn

def addQueue(type: str, link:str):
    global queueFiles
    global reposFiles
    global usersFiles
    if type =='repo':
        notFound=True
        if link in repo_urls: 
            notFound = False
            repo_urls[link] += 1
        else: 
            counter = 0
            while notFound and counter < reposFiles:
                pickleIn = open(f"api_scraper/seenRepos/{counter}.pickle", "rb")
                reposPickle = pickle.load(pickleIn)
                pickleIn.close()
                if link in reposPickle: 
                    notFound = False
                    reposPickle[link]+=1
                    pickleOut = open(f"api_scraper/seenRepos/{counter}.pickle", "wb")
                    pickle.dump(reposPickle, pickleOut)
                    pickleOut.close()
                counter+=1
        
        if notFound: 
            inQueue.append(["repo", link])
        
        if len(repo_urls) >= 1000:
            pickleOut = open(f"api_scraper/seenRepos/{reposFiles}.pickle", "wb")
            pickle.dump(repo_urls, pickleOut)
            pickleOut.close()
            with open(f"api_scraper/seenRepos/{reposFiles}.csv", "w", newline='') as file: 
                writer = csv.writer(file, delimiter='|')
                writer.writerows(repo_urls.items())
            repo_urls.clear()
            reposFiles += 1

    elif type == 'user':
        notFound=True
        if link in user_urls: 
            notFound = False
            user_urls[link] += 1
        counter = 0
        while notFound and counter < usersFiles:
            pickleIn = open(f"api_scraper/seenUsers/{counter}.pickle", "rb")
            usersPickle = pickle.load(pickleIn)
            pickleIn.close()
            if link in usersPickle: 
                notFound = False
                usersPickle[link]+=1
                pickleOut = open(f"api_scraper/seenUsers/{counter}.pickle", "wb")
                pickle.dump(usersPickle, pickleOut)
                pickleOut.close()
            counter+=1
        
        if notFound: 
            inQueue.append(["user", link])
        
        if len(user_urls) >= 1000:
            pickleOut = open(f"api_scraper/seenUsers/{usersFiles}.pickle", "wb")
            pickle.dump(user_urls, pickleOut)
            pickleOut.close()
            with open(f"api_scraper/seenUsers/{usersFiles}.csv", "w", newline='') as file: 
                writer = csv.writer(file, delimiter='|')
                writer.writerows(user_urls.items())
            user_urls.clear()
            usersFiles += 1

    else: raise ValueError("'type' must be 'repo' or 'user'")


    if len(inQueue) >= 1000:
        with open(f"api_scraper/queue/{queueFiles}.csv", "w", newline='') as file: 
            writer = csv.writer(file, delimiter='|')
            writer.writerows(inQueue)
        queueFiles += 1
        inQueue.clear()

def saveData():
    '''
    Helper function that saves the different lists in case of a crash.
        * queue
        * bigrams
        * seenUsers
        * seenRepos
    '''
    pickleOut = open(f"api_scraper/savedRun.pickle", "wb")
    pickle.dump([inQueue,bigrams,user_urls,repo_urls,usersFiles, reposFiles, queueFiles, currentQueue], pickleOut)
    pickleOut.close()

    pickleQueue = open(f"api_scraper/queue.pickle", "wb")
    pickle.dump(inQueue, pickleQueue)
    pickleQueue.close()
    
    pickleBigrams = open(f"api_scraper/bigrams.pickle", "wb")
    pickle.dump(bigrams, pickleBigrams)
    pickleBigrams.close()
    
    pickleUsers = open(f"api_scraper/seenUsers/{usersFiles}.pickle", "wb")
    pickle.dump(user_urls, pickleUsers)
    pickleUsers.close()
    with open(f"api_scraper/seenUsers/{usersFiles}.csv", "w",newline='') as file: 
        writer = csv.writer(file, delimiter='|')
        writer.writerows(user_urls.items())

    pickleRepos = open(f"api_scraper/seenRepos/{reposFiles}.pickle", "wb")
    pickle.dump(repo_urls, pickleRepos)
    pickleRepos.close()
    with open(f"api_scraper/seenRepos/{reposFiles}.csv", "w",newline='') as file: 
        writer = csv.writer(file, delimiter='|')
        writer.writerows(repo_urls.items())
    

def run(iterations):
    global currentQueue
    while iterations > 0:
        if not inQueue and queueFiles > 0:
            with open(f"api_scraper/queue/{currentQueue}.csv", newline='') as csvfile:
                reader = csv.reader(csvfile, delimiter='|')
                for row in reader:
                    inQueue.append(row)
            currentQueue += 1
        data = inQueue.pop()
        if data[0] == "user":
            getUserData(data[1])
        elif data[0] == "repo":
            getRepoData(data[1])
        else: 
            print(data)
            raise ValueError("'type' must be 'repo' or 'user'")
        iterations -= 1

    print(f"num users seen: \t\t{len(user_urls.items())}")
    print(f"num repos seen: \t\t{len(repo_urls.items())}")
    print(f"total remaining  in queue: \t{len(inQueue)}")
    with open(f"api_scraper/queue/{queueFiles}.csv", "w", newline='') as file: 
        writer = csv.writer(file, delimiter='|')
        writer.writerows(inQueue)

run(10)

with open("api_scraper/repos.csv", newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter='|')
    for row in reader:
        print(" | ".join(row))