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


timerDir = os.path.join( os.path.abspath(dir_), "timers")
timerFilePath = os.path.join(timerDir, "timers")
fourmPath = os.path.join( os.path.abspath(dir_), "fourms")

def createRaidTimer(timerData):
    raidTimerFile = open(os.path.join(timerDir, 'raid.json'), 'w+')
    json.dump(timerData, raidTimerFile)

def saveRaidTimer(timerData):
    raidTimerFile = open(os.path.join(timerDir, 'raid.json'), 'w+')
    json.dump(timerData, raidTimerFile)

def deleteRaidTimer():
    raidTimerFile = open(os.path.join(timerDir, 'raid.json'), 'w+')
    raidTimerFile.close()

def readRaid():
    try:
        raidTimerFile = open(os.path.join(timerDir, 'raid.json'), 'r')
        raidTimerJSON = json.load(raidTimerFile)
        raidTimerFile.close()
        return raidTimerJSON
    except:
        return -1

def readSpecificRaidTimer(raidTimer):
    try:
        raidTimerFile = open(os.path.join(fourmPath, raidTimer), 'r')
        raidTimer = raidTimerFile.readline()
        raidTimerFile.close()
        return raidTimer
    except:
        return -1

def readSpecificRaidTimerData(raidTimer):
    try:
        raidTimerFile = open(os.path.join(fourmPath, raidTimer + ".responses"), 'r')
        raidTimer = raidTimerFile.readline()
        raidTimerFile.close()
        return raidTimer
    except:
        return -1


def updateAcceptedUserList(timerData):
    userFile = open(os.path.join(timerDir, 'acceptedUsers.json'), 'w+')
    json.dump(timerData, userFile)

def readAcceptedUserList():
    try:
        userFile = open(os.path.join(timerDir, 'acceptedUsers.json'), 'r')
        userJSON = json.load(userFile)
        return userJSON
    except:
        return -1

def createRaffleTimer(timerData):
    raffleTimerFile = open(os.path.join(timerDir, 'raffle.json'), 'w+')
    json.dump(timerData, raffleTimerFile)

def readRaffle():
    try:
        raffleTimerFile = open(os.path.join(timerDir, 'raffle.json'), 'r')
        raffleJSON = json.load(raffleTimerFile)
        return raffleJSON
    except:
        return -1

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
