import requests
from datetime import datetime, timedelta
from collections import Counter

file = open("api_scraper/TOKEN.txt")
token=file.read()
file.close()
headers = {'Authorization': 'token ' + token}

login = requests.get('https://api.github.com/user', headers=headers)
link = "https://api.github.com/repos/torvalds/linux/stargazers"

response =  requests.get(link, headers=headers)
respJSON = response.json()
print(response.links)