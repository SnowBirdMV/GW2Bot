import requests
import json
from pprint import pprint
import asyncio
import os
import sys
import _json

if getattr(sys, 'frozen', False):
    # frozen
    dir_ = os.path.dirname(sys.executable)
else:
    # unfrozen
    dir_ = os.path.dirname(os.path.realpath(__file__))

APIKeyDir = logPath = os.path.join( os.path.abspath(dir_), "APIKeys")
APIKeyFilePath = logPath = os.path.join(APIKeyDir, "APIKeys")
timerDir = logPath = os.path.join( os.path.abspath(dir_), "timers")
timerFilePath = logPath = os.path.join(timerDir, "timers")

def deleteTimer(senderID, timerList):
    try:
        del timerList[senderID]
        return True
    except KeyError:
        return False

def checkTimer(id, timerList, key):
    if id in timerList:
        killCount = getInfo(key)
        return killCount - timerList[id]
    else:
        timerList[id] = getInfo(key)
        return False

def checkTotalKills(id, timerList, key):
    if id in timerList:
        killCount = getInfo(key)
        return timerList[id]
    else:
        timerList[id] = getInfo(key)
        return False


def startTimer(id, timerList, key):
    timerList[id] = getInfo(key)
    return timerList

def getInfo(key):
    info = requests.get("https://api.guildwars2.com/v2/account/achievements/?access_"
                             "token=" + key)
    infoJSON = info.json()
    for item in infoJSON:
        if item["id"] == 283:
            print(item["current"])
            return item["current"]
    pprint(infoJSON)
    return -1

def readAPIKeys():
    if not os.path.exists(APIKeyDir):
        os.makedirs(APIKeyDir)
    if os.path.isfile(APIKeyFilePath) and os.stat(APIKeyFilePath).st_size != 0:
        APIFile = open(APIKeyFilePath).read()
        APIData = json.loads(APIFile)
        pprint(APIData)
        return APIData

    else:
        return {}

def readTimers():
    if not os.path.exists(timerDir):
        os.makedirs(timerDir)
    if os.path.isfile(timerFilePath) and os.stat(timerFilePath).st_size != 0:
        timerFile = open(timerFilePath).read()
        timerData = json.loads(timerFile)
        pprint(timerData)
        return timerData

    else:
        return {}

def writeTimerList(timersToWrite):

    f = open(timerFilePath, "w+")
    json.dump(timersToWrite, f)

def writeAPIKeys(keysToWrite):

    f = open(APIKeyFilePath, "w+")
    json.dump(keysToWrite, f)
