import requests
from datetime import datetime, timedelta
from collections import Counter

file = open("api_scraper/TOKEN.txt")
token=file.read()
file.close()
headers = {'Authorization': 'token ' + token}

login = requests.get('https://api.github.com/user', headers=headers)
link = "https://api.github.com/users/misode/repos?per_page=100"

# Helper that converts datetime object into an integer
def time_to_int(dateObj: datetime):
    '''
    Converts a datetime obj into an integer timestamp.
    Args:
        dateObj (datetime): A datetime object
    Returns:
        timestamp (int): an integer timestamp
    '''
    return datetime.timestamp(dateObj)
# Helper that converts integers into datetime objects
def int_to_time(dateint:int):
    '''
    Converts an integer timestamp into a datetime object.
    Integer input of 0 returns datetime(1, 1, 1, 0, 0, 0)
    Args:
        timestamp (int): an integer timestamp
    Returns:
        dateObj (datetime): a datetime object
    '''
    if dateint == 0:
        return datetime(1, 1, 1, 0, 0, 0)
    UNIX_EPOCH = 719164
    dateobj = datetime.fromtimestamp(int(dateint))
    dateobj = dateobj - timedelta(days=UNIX_EPOCH)
    return dateobj

response =  requests.get(link, headers=headers)
respJSON = response.json()
print((response.links['next']['url']))