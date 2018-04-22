from __future__ import print_function
import requests
import json
from pprint import pprint
import os
from item import Item
from itemPrice import ItemPrice
from Account import Account
import operator
import math
from gUpgrade import guildUpgrade
import copy
import sys
import time
import shutil
import pprint
from TreasuryItem import TreasuryItem
from copy import deepcopy
import builtins

if getattr(sys, 'frozen', False):
    # frozen
    dir_ = os.path.dirname(sys.executable)
else:
    # unfrozen
    dir_ = os.path.dirname(os.path.realpath(__file__))

APIKey = "B1739385-6B19-344C-8DC3-B9717C4B778DC2240CCB-26CC-4885-9BE0-192A4039A895"
guildID = "0532959c-4f44-44d2-8168-a0c5a5f4b058"

logPath = os.path.join( os.path.abspath(dir_), "guildLogs", "guildLog")
logDirectory = os.path.join( os.path.abspath(dir_), "guildLogs")
treasuryPath = os.path.join( os.path.abspath(dir_), "guildProgress", "treasury")
UserTreasuryPath = os.path.join( os.path.abspath(dir_), "guildLogs", "treasury")
invitedPath = os.path.join( os.path.abspath(dir_), "guildLogs", "invited")
joinedPath = os.path.join( os.path.abspath(dir_), "guildLogs", "joined")
kickPath = os.path.join( os.path.abspath(dir_), "guildLogs", "kick")
upgradePath = os.path.join( os.path.abspath(dir_), "upgradeDatabase")
itemPricePath = os.path.join( os.path.abspath(dir_), "Items", "itemPrices")
stashPath = os.path.join( os.path.abspath(dir_), "guildLogs", "stash")
#globalTreasury = {}
#globalSHoppingList = {}
#golbalSum = {}
#globalPricePerPerson = {}

shoppingList = {}
list = {}
itemPrices = {}
upgradeList = {}
richTreasury = {}
sum = {}
itemPrices = {}
idList = {}
treasuryByUser = {}
pricePerPerson = {}
userRetention = {}
favorUpgrades = {}
gUpgradesJSON = {}
missingUpgrades = {}
curentUpgradeList = {}
favor = 0
gLevel = 0
aetherium = 0


def main():
    buildUpgradeDatabaseFromInternetTest()

    global list, itemPrices, upgradeList, richTreasury, sum, itemPrices, idList, treasuryByUser, pricePerPerson, userRetention, favorUpgrades, gUpgradesJSON, missingUpgrades, curentUpgradeList, shoppingList, ogUserList
    gUpgrades = requests.get("https://api.guildwars2.com/v2/guild/" + guildID + "/upgrades?access_"
                             "token=" + APIKey)
    gUpgradesJSON = gUpgrades.json()
    curentUpgradeList = gUpgradesJSON
    try:
        getLogFromInternet()
    except:
        pass
    global favor, gLevel, aetherium
    favor, gLevel, aetherium = getGuildInfo()
    shoppingList, idList, upgradeList, upgradeListByID, ignoreIDList = makeShoppingList()
    shoppingList, idList = addImagesToLists(shoppingList, idList)
    updateItemPricesTest(shoppingList)
    #updateItemPrices(shoppingList)
    itemPrices = createItemPriceList()
    upgradeList, upgradeListByID = addPricesToUpgradeList(upgradeList, upgradeListByID, itemPrices)
    updateTreasuryFromInternet()
    treasury, richTreasury, rawTreasury = buildTreasuryDict(idList, shoppingList)
    shoppingList = refineShoppingListFromTreasury(shoppingList, treasury)
    upgradeList = buildCurentUpgradeList(gUpgradesJSON, upgradeListByID, ignoreIDList)
    missingUpgrades = buildMissingUpgradeList(gUpgradesJSON, upgradeListByID, ignoreIDList)
    shoppingList = refineShoppingListFromUpgradeList(shoppingList, upgradeList)
    shoppingList = setListItemPrices(shoppingList, itemPrices)
    richTreasury = setListItemPrices(richTreasury, itemPrices)
    sum = calculateTotalCost(shoppingList, itemPrices)
    treasuryByUser = parseGuildTreasury(idList, itemPrices)
    pricePerPerson = treasuryCostByUser(treasuryByUser, itemPrices)
    userRetention, ogUserList = calculateRetention()
    expectedSum = calculateExpectedSum(upgradeList, richTreasury)
    #print(formatGoldAmount(expectedSum))
    #printPossibleUpgrades(missingUpgrades, richTreasury, favor) #no aetherium/level checks
    favorUpgrades = printFavorUpgrades(missingUpgrades, favor, gLevel, gUpgradesJSON)
    addPricesToGUpgrades()
    addPricesToFavorUpgrades()
    stashJSON = readStash()
    userGoldContributions = userContributions(stashJSON)
    debug = upgradeList
    listOfOGUsers = createListOfUsers(ogUserList)


    return list, itemPrices, upgradeList, richTreasury, sum, itemPrices, idList, treasuryByUser, pricePerPerson, userRetention, favorUpgrades, rawTreasury, ogUserList, userGoldContributions, listOfOGUsers

#buildUpgradeDatabaseFromInternet()

def addImagesToLists(shoppingList, idList):
    JSONList = []
    listOfIDs = builtins.list(idList.keys())
    chunkCount = math.ceil(len(listOfIDs) / 100)
    splitIDArray = chunkIt(listOfIDs, chunkCount)
    for chunk in splitIDArray:
        print("https://api.guildwars2.com/v2/items?ids=" + ",".join(map(str, chunk)))
        idRequest = requests.get("https://api.guildwars2.com/v2/items?ids=" + ",".join(map(str, chunk)))
        JSONList.append(idRequest.json())
    masterJSON = {}
    for item in JSONList:
        for i in item:
            masterJSON[i["id"]] = i
    for item in shoppingList:
        try:
            shoppingList[item].image = masterJSON[shoppingList[item].id]
        except KeyError:
            print(str(item) + " not in id list")
    for item in idList:
        try:
            idList[item].image = masterJSON[idList[item].id]
        except KeyError:
            print(str(item) + " not in id list")
    return shoppingList, idList


def createListOfUsers(userList):
    newUserList = {}
    for inviter in userList:
        for user in userList[inviter]:
            newUserList[user] = userList[inviter][user]
    return newUserList

def formatRaffleAChances(rafflePointList):
    output = ""
    longestLine = 0
    for user in rafflePointList:
        if len(user) > longestLine:
            longestLine = len(user)
    longestLine += 3
    output = "User"
    output += " " * (longestLine - len(output))
    output += "\n"
    for user in rafflePointList:
        curentLine = ""
        curentLine += user
        curentLine += " " * (longestLine - len(curentLine))
        curentLine += rafflePointList[user]
        output += curentLine
    return output




def userContributions(stashJSON):
    userList = {}
    for event in stashJSON:
        if event["coins"] > 0 and event["operation"] == "deposit":
            addToHash(userList, event["user"], event["coins"])
        elif event["coins"] > 0 and event["operation"] == "withdraw":
            subtractFromHash(userList, event["user"], event["coins"])
    test = userList
    #pprint.pprint(userList)
    return userList

def readStash():
    global stashPath
    stashJSON = json.load(open(stashPath))
    return stashJSON


def getAetherium():
    global aetherium
    return aetherium

def getFavor():
    global favor
    return favor

def getLevel():
    global gLevel
    return gLevel



def formatUserRetention(raw=False):
    if raw:
        global ogUserList
        userRetentionList = ogUserList
    else:
        global userRetention
        userRetentionList = userRetention
    output = ""
    longestLine = 0
    test = userRetention
    for key in userRetentionList:
        if len(key) > longestLine:
            longestLine = len(key)
    longestLine += 3
    for key in userRetentionList:
        if len(userRetentionList[key]) > 0:
            output += key + (" " * (longestLine - len(key) + 3)) + str(len(userRetentionList[key])) + "\n"
    return output

def itemInContributors(item):
    for user in treasuryByUser:
        if item in treasuryByUser[user]:
            return True
    return False

def formatItemList(itemList):
    output = ""
    line = ""
    longestLine = 0
    for key, item in itemList.items():
        if len(item.name) > longestLine:
            longestLine = len(item.name)
    longestLine += 3
    for key, item in itemList.items():
        line = item.name
        line += " " * (longestLine - len(line))
        line += str(item.amount)
        output += line + "\n"
    return output


def formatItemremaining(itemName, longestLine):
    total = 0
    found = 0
    output = ""
    global favorUpgrades
    global richTreasury
    for gUpgrade in favorUpgrades:
        if itemName in favorUpgrades[gUpgrade].ingredients:
            total += favorUpgrades[gUpgrade].ingredients[itemName].amount
            found = 1
    if found == 0:
        return itemName + " is not available to be added to the treasury."
    else:
        output += itemName
        while len(output) < longestLine:
            output += " "
        output += str(total)
        while len(output) < longestLine + 8:
            output += " "
        if itemName in richTreasury:
            output += str(total - richTreasury[itemName].amount)
        return output


def formatContributorItem(itemName):
    output = ""
    global treasuryByUser
    longestLine = longestUserInTreasureyContributors(3)
    header = "User"
    while len(header) < longestLine:
        header += " "
    header += "Amount  Cost"
    output += header + "\n"
    for user in treasuryByUser:
        if itemName in treasuryByUser[user]:
            output += formatUserItemContribution(itemName, user, treasuryByUser[user][itemName].amount, treasuryByUser[user][itemName].price.buyPrice, longestLine) + "\n"
    return output

def formatUserItemContribution(itemName, user, amount, price, longestLine):
    output = ""
    output += user
    while len(output) < longestLine:
        output += " "
    output += str(amount)
    while len(output) < longestLine + 8:
        output += " "
    output += formatGoldAmount(price * amount)
    return output

def longestUserInTreasureyContributors(offset=0):
    longestLine = 0
    for user in treasuryByUser:
        if len(user) > longestLine:
            longestLine = len(user)
    for i in range(0, offset):
        longestLine += 1
    return longestLine

def findLongestItemName(list):
    longestLine = 0
    for item in list:
        if len(item) > longestLine:
            longestLine = len(item)
    return longestLine + 3

def formatShoppingList(fullList=0):
    global shoppingList
    sortedList = sorted(shoppingList.items(), key=lambda x: x[1].name, reverse=False)
    longestLine = 0
    for item in shoppingList:
        if len(shoppingList[item].name) > longestLine:
            longestLine = len(shoppingList[item].name)
    longestLine += 3
    returnString = "Item"
    while len(returnString) < longestLine:
        returnString += " "
    returnString += "Amount"
    while len(returnString) < longestLine + 8:
        returnString += " "
    returnString += "Cost\n"
    for upgrade in sortedList:
        if fullList:
            returnString += formatItemCost(upgrade[1], upgrade[1].amount, longestLine) + "\n"
        else:
            if upgrade[1].amount > 0:
                returnString += formatItemCost(upgrade[1], upgrade[1].amount, longestLine) + "\n"
    return returnString

def formatUserContribution(user):
    global treasuryByUser
    outputString = ""
    longestLine = 0
    sortedList = sorted(treasuryByUser[user].items(), key=lambda x: x[1].name)
    count = 0
    for item in sortedList:
        if len(sortedList[count][1].name) > longestLine:
            longestLine = len(sortedList[count][1].name)
        count += 1
    longestLine += 3
    count = 0
    for item in sortedList:
        outputString += sortedList[count][1].name
        for i in range(0, longestLine - len(sortedList[count][1].name)):
            outputString += " "
        outputString += str(sortedList[count][1].amount)
        for i in range(0, 7 - len(str(sortedList[count][1].amount))):
            outputString += " "
        outputString += formatGoldAmount(sortedList[count][1].amount * sortedList[count][1].price.buyPrice) + "\n"
        count += 1

    return outputString

def userInTreasury(username):
    global treasuryByUser
    returnString = ""
    upgrades = any(key.startswith(username) for key in treasuryByUser)
    #[(k, v) for (k, v) in favorUpgrades.iteritems() if upgradeName in k]
    user = searchUsers(treasuryByUser, username)
    return user

def formatCheapestUpgradesByTotalCost():
    global favorUpgrades
    sortedList = sorted(favorUpgrades.items(), key=lambda x: x[1].totalPrice, reverse=True)
    returnString = "Upgrade"
    longestLine = 0
    for upgrade in favorUpgrades:
        if len(favorUpgrades[upgrade].name) > longestLine:
            longestLine = len(favorUpgrades[upgrade].name)
    longestLine += 3
    while len(returnString) < longestLine:
        returnString += " "
    returnString += "Cost\n"
    for upgrade in sortedList:
        returnString += formatUpgradeCostTotal(upgrade[1], longestLine) + "\n"
    return returnString

def formatCheapestUpgradesByCurentCost():
    global favorUpgrades
    test = favorUpgrades
    sortedList = sorted(favorUpgrades.items(), key=lambda x: x[1].curentPrice, reverse=True)
    longestLine = 0
    for upgrade in favorUpgrades:
        if len(favorUpgrades[upgrade].name) > longestLine:
            longestLine = len(favorUpgrades[upgrade].name)
    longestLine += 3
    returnString = "Upgrade"
    while len(returnString) < longestLine:
        returnString += " "
    returnString += "Cost\n"
    for upgrade in sortedList:
        returnString += formatUpgradeCost(upgrade[1], longestLine) + "\n"
    return returnString

def formatAllUpgradesByCurentCost():
    global missingUpgrades
    localList = missingUpgrades
    sortedList = sorted(localList.items(), key=lambda x: x[1].curentPrice, reverse=True)
    longestLine = 0
    for upgrade in localList:
        if len(localList[upgrade].name) > longestLine:
            longestLine = len(localList[upgrade].name)
    longestLine += 3
    returnString = "Upgrade"
    while len(returnString) < longestLine:
        returnString += " "
    returnString += "Cost\n"
    for upgrade in sortedList:
        returnString += formatUpgradeCost(upgrade[1], longestLine) + "\n"
    return returnString

def formatItemCost(item, amount, longestLine):
    lineToAdd = item.name

    while len(lineToAdd) < longestLine:
        lineToAdd += " "
    lineToAdd += str(amount)
    while len(lineToAdd) < longestLine + 8:
        lineToAdd += " "
    lineToAdd +=formatGoldAmount(item.price.buyPrice * amount)
    return lineToAdd

def formatUpgradeCost(upgrade, longestLine):
    lineToAdd = upgrade.name

    while len(lineToAdd) < longestLine:
        lineToAdd += " "
    lineToAdd +=formatGoldAmount(upgrade.curentPrice)
    return lineToAdd

def formatUpgradeCostTotal(upgrade, longestLine):
    lineToAdd = upgrade.name
    while len(lineToAdd) < longestLine:
        lineToAdd += " "
    lineToAdd +=formatGoldAmount(upgrade.totalPrice)
    return lineToAdd

def upgradeInList(upgradeName):
    return search(favorUpgrades, upgradeName)

def missingUpgradeInList(upgradeName):
    return search(missingUpgrades, upgradeName)

def formatNeededUpgradeSearch(upgradeName):
    returnString = ""
    #[(k, v) for (k, v) in favorUpgrades.iteritems() if upgradeName in k]
    upgrade = search(favorUpgrades, upgradeName)
    if upgrade:
        returnString += formatGUpgradeTreasury(upgrade[0], True) + "\n"
    return returnString

def formatAllUpgradeSearch(upgradeName):
    global missingUpgrades
    returnString = ""
    #[(k, v) for (k, v) in favorUpgrades.iteritems() if upgradeName in k]
    upgrade = search(missingUpgrades, upgradeName)
    if upgrade:
        returnString += formatGUpgradeTreasury(upgrade[0], allUpgrades=True) + "\n"
    return returnString

def itemInList(upgradeName):
    return findItems(favorUpgrades, upgradeName)

def itemInShoppingList(upgradeName):
    return findItemsInList(shoppingList, upgradeName)

def findItemsInList(values, searchFor):
    foundList = []
    for item in searchFor:
        if item in values:
            foundList.append(item)
    if foundList == []:
        return []
    else:
        return foundList

def findItems(values, searchFor):
    foundList = []
    for upgrade in values:
        for k in values[upgrade].ingredients:
            if searchFor.lower() in values[upgrade].ingredients[k].name.lower():
                if k not in foundList:
                    foundList.append(values[upgrade].ingredients[k].name)
    if foundList == []:
        return None
    else:
        return foundList

def search(values, searchFor):
    foundList = []
    for k in values:
        if searchFor.lower() in values[k].name.lower():
            foundList.append(values[k])
    if foundList == []:
        return None
    else:
        return foundList

def searchUsers(values, searchFor):
    for k in values:
        if searchFor.lower() in k.lower():
            return k
    return None

def addPricesToFavorUpgrades():
    global favorUpgrades
    for item in favorUpgrades:
        debug = favorUpgrades[item]
        favorUpgrades[item].totalPrice = upgradeCost(favorUpgrades[item])
        favorUpgrades[item].curentPrice = remainingPriceCheckGUpgrade(favorUpgrades[item])
        #print(str(favorUpgrades[item].totalPrice) + str(favorUpgrades[item].curentPrice))

def addPricesToGUpgrades():
    global missingUpgrades
    for item in missingUpgrades:
        missingUpgrades[item].totalPrice = upgradeCost(missingUpgrades[item])
        missingUpgrades[item].curentPrice = remainingPriceCheckGUpgrade(missingUpgrades[item])
        #print(str(favorUpgrades[item].totalPrice) + str(favorUpgrades[item].curentPrice))

def upgradeCost(gUpgrade):
    price = 0
    tempPrice = 0
    for ingredient in gUpgrade.ingredients:
        item = gUpgrade.ingredients[ingredient]
        if ingredient in richTreasury:
            tempPrice = item.amount
            price += tempPrice * itemPrices[ingredient].buyPrice
        elif ingredient == "Aetherium":
            pass
        elif ingredient == "Guild Favor":
            pass
        else:
            pass
        tempPrice = 0
    return price

def remainingPriceCheckGUpgrade(gUpgrade):
    price = 0
    tempPrice = 0
    for ingredient in gUpgrade.ingredients:
        item = gUpgrade.ingredients[ingredient]
        if ingredient in richTreasury:
            if item.amount - richTreasury[ingredient].amount > 0:
                tempPrice = item.amount - richTreasury[ingredient].amount
                price += tempPrice * itemPrices[ingredient].buyPrice
        elif ingredient == "Aetherium":
            pass
        elif ingredient == "Guild Favor":
            pass
        else:
            pass
        tempPrice = 0
    return price

def formatGUpgradeTreasury(gUpgrade, showEmpty=0, allUpgrades=0):
    finalString = "Item Name"
    longestLine = len("Item Name")
    for item in gUpgrade.ingredients:
        if len(gUpgrade.ingredients[item].name) > longestLine:
            longestLine = len(gUpgrade.ingredients[item].name)
    longestLine += 3
    for i in range(0, longestLine -len("Item Name")):
        finalString += " "
    if allUpgrades:
        finalString += "Amount   Price\n"
    else:
        finalString += "Amount   Needed   Price\n"
    returnString = ""
    passed = 0
    for ingredient in gUpgrade.ingredients:
        item = gUpgrade.ingredients[ingredient]
        returnString += item.name
        for i in range(0, longestLine - len(item.name)):
            returnString += " "
        if ingredient in richTreasury:
            if item.amount - richTreasury[ingredient].amount > 0 or showEmpty:
                returnString += str(item.amount)
                for i in range(0, 9 - len(str(item.amount))):
                    returnString += " "
                if not allUpgrades:
                    if item.amount - richTreasury[ingredient].amount > 0:
                        returnString += str(item.amount - richTreasury[ingredient].amount)
                    else:
                        returnString += "0"
                    for i in range(0, 9 - len(str(item.amount - richTreasury[ingredient].amount))):
                        returnString += " "



                if item.amount - richTreasury[ingredient].amount > 0:
                    returnString += formatGoldAmount((item.amount - richTreasury[ingredient].amount) * item.price.buyPrice)
                passed = 1
        elif ingredient == "Aetherium":
            if item.amount - aetherium > 0:
                returnString += str(item.amount)
                if not allUpgrades:
                    for i in range(0, 9 - len(str(item.amount - aetherium))):
                        returnString += " "
                    if item.amount - aetherium < 0:
                        returnString += "0"
                    else:
                        returnString += str(item.amount - aetherium)
                passed = 1
        elif ingredient == "Guild Favor":
            returnString += str(item.amount)
            if not allUpgrades:
                for i in range(0, 9 - len(str(item.amount))):
                    returnString += " "
                if item.amount - favor < 0:
                    returnString += "0"
                else:
                    returnString += str(item.amount - favor)
            passed = 1
        else:
            returnString += str(item.amount)
            for i in range(0, 9 - len(str(item.amount))):
                returnString += " "
            returnString += formatGoldAmount(item.amount * item.price.buyPrice)
            passed = 1

        if passed:
            finalString += returnString + "\n"
        passed = 0
        returnString = ""
    return finalString

def formatGUpgrade(gUpgrade):
    finalString = gUpgrade.name + "\n"
    returnString = ""
    for item in gUpgrade.ingredients:
        if len(gUpgrade.ingredients[item].name) > longestLine:
            longestLine = len(gUpgrade.ingredients[item].name)
    for ingredient in gUpgrade.ingredients:
        item = gUpgrade.ingredients[ingredient]
        returnString += item.name
        for i in range(0, longestLine - len(item.name)):
            returnString += " "
        returnString += str(item.amount)
        finalString += returnString + "\n"
        returnString = ""
    return finalString


def printFavorUpgrades(missingUpgrades, favor, gLevel, curentUpgradeList):
    newUpgradeList = {}
    #print("-----------------------")
    for upgrade in missingUpgrades:
        if missingUpgrades[upgrade].ingredients["Guild Favor"].amount < favor:
            if missingUpgrades[upgrade].level <= gLevel:
                if is_slice_in_list(missingUpgrades[upgrade].prerequisites, curentUpgradeList):
                    newUpgradeList[upgrade] = missingUpgrades[upgrade]
                    #print(upgrade, newUpgradeList[upgrade].ingredients["Guild Favor"].amount)
                    for item in newUpgradeList[upgrade].ingredients:
                        tempItem = newUpgradeList[upgrade].ingredients[item]
                        #print("    " + tempItem.name + ": " + str(tempItem.amount))
    #print("-----------------------")
    return newUpgradeList

def formatFavorUpgradesLongGlobal():
    global missingUpgrades, favor, gLevel, curentUpgradeList
    newUpgradeList = {}
    formattedString = ""
    longestLine = 0
    for upgrade in missingUpgrades:
        if len(missingUpgrades[upgrade].name) > longestLine:
            longestLine = len(missingUpgrades[upgrade].name)
    #print("-----------------------")
    for upgrade in missingUpgrades:
        lineToAdd = ""
        if missingUpgrades[upgrade].ingredients["Guild Favor"].amount < favor:
            if missingUpgrades[upgrade].level <= gLevel:
                if is_slice_in_list(missingUpgrades[upgrade].prerequisites, curentUpgradeList):
                    newUpgradeList[upgrade] = missingUpgrades[upgrade]
                    #print(upgrade, newUpgradeList[upgrade].ingredients["Guild Favor"].amount)
                    if len(upgrade) > longestLine:
                        longestLine = len(upgrade)
                    lineToAdd = "\n" + upgrade + "\n"
                    formattedString += lineToAdd
                    lineToAdd = ""
                    for item in newUpgradeList[upgrade].ingredients:
                        tempItem = newUpgradeList[upgrade].ingredients[item]
                        lineToAdd += "    " + tempItem.name
                        while len(lineToAdd) < longestLine:
                            lineToAdd += " "
                        lineToAdd += str(tempItem.amount) + "\n"
                        formattedString += lineToAdd
                        lineToAdd = ""
        lineToAdd = ""
    #print("-----------------------")
    return formattedString

def formatFavorUpgradesGlobal():
    global missingUpgrades, favor, gLevel, curentUpgradeList
    newUpgradeList = {}
    formattedString = ""
    longestLine = 0
    for upgrade in missingUpgrades:
        if len(missingUpgrades[upgrade].name) > longestLine:
            longestLine = len(missingUpgrades[upgrade].name)
    #print("-----------------------")
    for upgrade in missingUpgrades:
        if missingUpgrades[upgrade].ingredients["Guild Favor"].amount < favor:
            if missingUpgrades[upgrade].level <= gLevel:
                if is_slice_in_list(missingUpgrades[upgrade].prerequisites, curentUpgradeList):
                    newUpgradeList[upgrade] = missingUpgrades[upgrade]
                    #print(upgrade, newUpgradeList[upgrade].ingredients["Guild Favor"].amount)
                    if len(upgrade) > longestLine:
                        longestLine = len(upgrade)
                    lineToAdd = upgrade
                    while len(lineToAdd) < longestLine:
                        lineToAdd += " "
                    lineToAdd +=str(newUpgradeList[upgrade].ingredients["Guild Favor"].amount) + "     "  + str(newUpgradeList[upgrade].ingredients["Aetherium"].amount) + "\n"
                    formattedString += lineToAdd
        lineToAdd = ""
    #print("-----------------------")
    return formattedString

def getGuildInfo():
    guildRequests = requests.get("https://api.guildwars2.com/v2/guild/" + guildID + "?access_token=" + APIKey)
    guildJSON = guildRequests.json()
    try:
        test = guildJSON["error"]
        return 0, 0, 0
    except:
        pass
    return guildJSON["favor"], guildJSON["level"], guildJSON["aetherium"]




def buildMissingUpgradeList(upgradeList, totalUpgradeListByID, ignoreIDList):
    newUpgradeList = {}
    for id in totalUpgradeListByID:
        if id not in ignoreIDList:
            if id not in upgradeList:
                name = totalUpgradeListByID[id].name
                newUpgradeList[name] = totalUpgradeListByID[id]
    return newUpgradeList

def printPossibleUpgrades(upgradeList, treasury, favor):
    found = 0
    for upgrade in upgradeList:
        test = upgradeList
        for item in upgradeList[upgrade].ingredients:
            if item not in treasury:
                if item == "Guild Favor":
                    if upgradeList[upgrade].ingredients[item].amount > favor:
                        found = 1
                #print(item)
                elif item == "Aetherium":
                    #add aetherium requirement?
                    pass
                else:
                    found = 1
                    break
            else:
                if treasury[item].amount >= upgradeList[upgrade].ingredients[item].amount:
                    pass
                else:
                    found = 1
                    break
        if not found:
            print(upgrade + " passed" + " " + str(upgradeList[upgrade].ingredients["Guild Favor"].amount))

        found = 0
    print("\n")
    return


def addPricesToUpgradeList(upgradeList, upgradeListByID, itemPrices):
    for upgrade in upgradeList:
        for item in upgradeList[upgrade].ingredients:
            if item not in itemPrices:
                #eprint(item, "not in price list!")
                pass
            else:
                upgradeListByID[upgradeList[upgrade].id].ingredients[item].price = itemPrices[item]
                upgradeList[upgrade].ingredients[item].price = itemPrices[item]
    return upgradeList, upgradeListByID

def calculateExpectedSum(upgradeList, treasury):
    sum = 0
    for upgrade in upgradeList:
        for item in upgradeList[upgrade].ingredients:
            if upgradeList[upgrade].ingredients[item].price is not None:
                sum += upgradeList[upgrade].ingredients[item].price.sellPrice * upgradeList[upgrade].ingredients[item].amount
    for item in treasury:
        sum += treasury[item].price.sellPrice * treasury[item].amount
    return sum

def calculateRetention():
    os.chdir(os.path.join( os.path.abspath(dir_), "guildLogs"))
    f = open(invitedPath)
    invitedJSON = json.load(f)
    userDict = {}
    for item in invitedJSON:
        user = item["user"]
        invitedBy = item["invited_by"]
        time = item["time"]
        if invitedBy not in userDict:
            userDict[invitedBy] = {}
        userDict[invitedBy][user] = Account(user, invitedBy, time, None)
    ogUserDict = deepcopy(userDict)

    f = open(joinedPath)
    joinedJSON = json.load(f)

    refinedUserDict = {}
    for user in userDict:
        refinedUserDict[user] = {}

    for item in joinedJSON:
        user = item["user"]
        for inviterDict in userDict:
            if user in userDict[inviterDict]:
                refinedUserDict[inviterDict][user] = Account(inviterDict, user, userDict[inviterDict][user].dateAdded, item["time"])
                break




    f = open(kickPath)
    kickedJSON = json.load(f)

    for item in kickedJSON:
        user = item["user"]
        for inviterDict in refinedUserDict:
            if user in refinedUserDict[inviterDict]:
                del refinedUserDict[inviterDict][user]
                break

    return refinedUserDict, ogUserDict




def treasuryCostByUser(userDict, itemPrices):
    pricePerPerson = {}
    for user in userDict:
        totalPrice = 0
        for item in userDict[user]:
            totalPrice += itemPrices[item].sellPrice * userDict[user][item].amount
        pricePerPerson[user] = formatGoldAmount(totalPrice)
    return pricePerPerson

def formattreasuryCostByUser():
    global treasuryByUser, itemPrices
    outputString = ""
    pricePerPerson = {}
    longestLine = 0
    for user in treasuryByUser:
        if len(user) > longestLine:
            longestLine = len(user)
    longestLine += 3
    for user in treasuryByUser:
        totalPrice = 0
        for item in treasuryByUser[user]:
            totalPrice += itemPrices[item].sellPrice * treasuryByUser[user][item].amount
        pricePerPerson[user] = totalPrice
    sortedList = sorted(pricePerPerson.items(), key=lambda x: x[1], reverse=True)
    realOutputString = ""
    for item in sortedList:
        realOutputString += item[0]
        for i in range(0, longestLine - len(item[0])):
            realOutputString += " "
        realOutputString += formatGoldAmount((item[1])) + "\n"
    return realOutputString

def parseGuildTreasury(idList, itemPrices):
    os.chdir(os.path.dirname(os.path.join(os.path.abspath(dir_), "guildLogs")))
    f = open(UserTreasuryPath, "r")
    treasuryJSON = json.load(f)
    userDict = {}
    for item in treasuryJSON:
        user = item["user"]
        itemID = item["item_id"]
        amount = item["count"]
        name = idList[itemID].name
        if user not in userDict:
            userDict[user] = {}
        newItem = copy.deepcopy(idList[itemID])
        if itemID in userDict[user]:
            newItem.amount = amount + userDict[user][item["item_id"]].amount
        else:
            newItem.amount = amount
        userDict[user][item["item_id"]] = newItem
    for user in userDict:
        newHash = {}
        for item in userDict[user]:
            addItemToHash(newHash, userDict[user][item].name, userDict[user][item].id, userDict[user][item].amount, userDict[user][item].image)
        userDict[user] = newHash
        for item in userDict[user]:
            itemID = userDict[user][item].id
            name = userDict[user][item].name
            userDict[user][item].price = newItem.price = ItemPrice(itemID, userDict[user][item].name, itemPrices[name].buyPrice, itemPrices[name].sellPrice)


    return userDict

def getLogFromInternet():
    os.chdir(os.path.dirname(os.path.join( os.path.abspath(dir_) , "guildLogs")))
    #print("https://api.guildwars2.com/v2/guild/" + guildID + "/log?access_"
                             #"token=" + APIKey)
    log = requests.get("https://api.guildwars2.com/v2/guild/" + guildID + "/log?access_"
                             "token=" + APIKey)
    logDict = {}
    if not os.path.exists(logPath) or not os.path.getsize(logPath) > 0:
        f = open(logPath, "w")
        f.write(log.text)
        for item in log.json():
            logDict[item["id"]] = json.dumps(item)
        f.close()
    else:
        for item in log.json():
            logDict[item["id"]] = item
        f = open(logPath, "r")
        logJSON = json.load(f)
        for item in logJSON:
            if item not in logDict:
                logDict[item] = logJSON[item]




    f = open(logPath, "r")
    logJSON = json.load(f)
    for item in logJSON:
        if isinstance(item, str):
            if isinstance(logJSON[item], str):
                logJSON[item] = json.loads(logJSON[item])
            else:
                pass
        else:
            pass
    newLog = log.json()
    for item in newLog:
        if item["id"] not in logDict:
            logDict[item["id"]] = json.dumps(item)
    for item in log.json():
        if item["id"] not in logDict:
            logDict[item["id"]] = json.dumps(item)

    for item in logDict:
        if isinstance(item, str):
            if isinstance(logDict[item], str):
                logDict[item] = json.loads(logDict[item])
            else:
                pass
        else:
            pass


    f.close()

    f = open(logPath, "w")
    f.write(json.dumps(logDict))
    f.close()
    os.chdir(os.path.join( os.path.abspath(dir_) , "guildLogs"))
    f = open(logPath, "r")
    logJSON = json.load(f)

    for item in logDict:
        if isinstance(item, str):
            if isinstance(logDict[item], str):
                logDict[item] = json.loads(logDict[item])
            else:
                pass
        else:
            pass


    categories = {}
    for item in logDict:
        addToHash(categories,logDict[item]["type"], 1)

    parseGuildLog()
    pprint.pprint(categories)
    f.close()
    return logDict
    #f.write(log.text)

def printLogCategories(logDict):
    categories = {}
    for item in logDict:
        addToHash(categories, logDict[item]["type"], 1)
    #pprint(categories)


def parseGuildLog():
    os.chdir(os.path.join( os.path.abspath(dir_), "guildLogs"))
    f = open(logPath, "r")
    logJSON = json.load(f)
    categories = {}

    guildLogDict = {}
    file = open(upgradePath, "w+")
    file.write("[")
    counter = 1
    files = []
    fileNames = []
    fileIndices = []
    for logItem in logJSON:
        if logJSON[logItem]["type"] not in fileNames:
            fileNames.append(logJSON[logItem]["type"])
            files.append(open(logJSON[logItem]["type"], "w"))
            fileIndices.append(0)
        fileName = logJSON[logItem]["type"]
        curentMetaIndex = fileNames.index(fileName)
        curentFile = files[curentMetaIndex]
        curentIndex = fileIndices[curentMetaIndex]
        if curentIndex == 0:
            curentFile.write("[\n")
        else:
            curentFile.write(",\n")

        output = json.dumps(logJSON[logItem])
        curentFile.write(output)
        counter += 1
        fileIndices[curentMetaIndex] += 1
    for item in files:
        #print(item.name)
        item.write("\n]")
        item.close()




def setListItemPrices(itemList, itemPrices):
    for item in itemList:
        if item not in itemPrices:
            itemList[item].price = ItemPrice(None, item, 0, 0)
        else:
            itemList[item].price = itemPrices[item]
    return itemList

def buildCurentUpgradeList(curentUpgradeList, totalUpgradeListByID, ignoreIDList):
    newUpgradeList = {}
    for id in curentUpgradeList:
        if id not in ignoreIDList:
            name = totalUpgradeListByID[id].name
            newUpgradeList[name] = totalUpgradeListByID[id]
    return newUpgradeList


def refineShoppingListFromUpgradeList(itemList, gUpgradeList):
    for item in gUpgradeList:
        for name in gUpgradeList[item].ingredients:
            material = gUpgradeList[item].ingredients[name]
            itemList[name].amount = itemList[name].amount - material.amount
    return itemList

def buildTreasuryDict(idList, itemList):
    os.chdir(os.path.join(os.path.abspath(dir_), "guildProgress"))
    treasuryFile = open(treasuryPath)
    treasuryJSON = json.load(treasuryFile)
    treasuryDict = {}
    richTreasuryDict = {}
    rawTreasuryDict = {}
    try:
        test = treasuryJSON["error"]
        return {}, {}, {}
    except:
        pass
    for item in treasuryJSON:
        itemID = item["item_id"]
        itemAmount = item["count"]
        try:
            treasuryDict[idList[itemID].name] = itemAmount
        except:
            print("Errored but im putting a bandaid on it")
            continue
        newItem = copy.deepcopy(itemList[idList[itemID].name])
        newItem.amount = itemAmount
        richTreasuryDict[idList[itemID].name] = newItem
        total = 0
        for count in item["needed_by"]:
            total += count["count"]
        rawTreasuryDict[idList[itemID].name] = TreasuryItem(itemID, idList[itemID].name, total, itemAmount, newItem)
    return treasuryDict, richTreasuryDict, rawTreasuryDict

def refineShoppingListFromTreasury(itemList, treasuryList):
    for item in treasuryList:
        itemList[item].amount = itemList[item].amount - treasuryList[item]
    return itemList



def buildUpgradeDatabaseFromInternet():
    gUpgradeList = requests.get("https://api.guildwars2.com/v2/guild/upgrades").json()
    gUpgradeDict = {}
    file = open(upgradePath, "w")
    file.write("[")
    counter = 1
    #print("Updating guild upgrade database.  This will take a while")
    files = []
    fileNames = []
    fileIndices = []
    for id in gUpgradeList:
        curentUpgrade = requests.get("https://api.guildwars2.com/v2/guild/upgrades/" + str(id))
        curentUpgradeJSON = curentUpgrade.json()
        print(curentUpgradeJSON["type"])
        if curentUpgradeJSON["type"] not in fileNames:
            fileNames.append(curentUpgradeJSON["type"])
            files.append(open(curentUpgradeJSON["type"], "w"))
            fileIndices.append(0)
        fileName = curentUpgradeJSON["type"]
        curentMetaIndex = fileNames.index(fileName)
        curentFile = files[curentMetaIndex]
        curentIndex = fileIndices[curentMetaIndex]
        if curentIndex == 0:
            curentFile.write("[\n")
        else:
            curentFile.write(",\n")

        #print(counter, "/", len(gUpgradeList))
        curentFile.write(curentUpgrade.text)
        counter += 1
        fileIndices[curentMetaIndex] += 1
    for item in files:
        item.write("\n]")

def buildUpgradeDatabaseFromInternetTest():
    gUpgradeList = requests.get("https://api.guildwars2.com/v2/guild/upgrades").json()
    gUpgradeDict = {}
    file = open(upgradePath, "w")
    file.write("[")
    counter = 1
    print("Updating guild upgrade database.  This will take a while")
    files = []
    fileNames = []
    fileIndices = []
    chunkCount = len(gUpgradeList) / 200
    chunkCount = math.ceil(chunkCount)
    gUpgradeChunks = chunkIt(gUpgradeList, chunkCount)
    for subList in gUpgradeChunks:
        urlStringAdd = ','.join(map(str, subList))
        curentUpgrade = requests.get("https://api.guildwars2.com/v2/guild/upgrades?ids=" + urlStringAdd)
        #print("https://api.guildwars2.com/v2/guild/upgrades?ids=" + urlStringAdd)
        curentUpgradeJSON = curentUpgrade.json()
        for item in curentUpgradeJSON:
            if item["type"] not in fileNames:
                fileNames.append(item["type"])
                #print(item["type"])
                files.append(open(os.path.join(logDirectory, item["type"]), "w"))
                fileIndices.append(0)
            fileName = item["type"]
            curentMetaIndex = fileNames.index(fileName)
            curentFile = files[curentMetaIndex]
            curentIndex = fileIndices[curentMetaIndex]
            if curentIndex == 0:
                curentFile.write("[\n")
            else:
                curentFile.write(",\n")

            #print(counter, "/", len(gUpgradeList))
            curentFile.write(curentUpgrade.text)
            counter += 1
            fileIndices[curentMetaIndex] += 1
    for item in files:
        item.write("\n]")

    return

def updateTreasuryFromInternet():
    os.chdir(os.path.join(os.path.abspath(dir_), "guildProgress"))
    treasuryText = requests.get("https://api.guildwars2.com/v2/guild/" + guildID + "/treasury?access_token=" + APIKey)
    outputFile = open(treasuryPath, "w")
    outputFile.write(treasuryText.text)

def getUpgradeIDList():
    os.chdir(os.path.join(os.path.abspath(dir_), "guildLogs"))



def updateItemPricesTest(ShoppingList):
    os.chdir(os.path.join(os.path.abspath(dir_), "Items"))
    print("Updating price list.")
    counter = 1

    total = len(ShoppingList)
    coutner = 1
    idArray = []
    for item in ShoppingList:
        idArray.append(ShoppingList[item].id)
    chunkCount = math.ceil(len(idArray)/100)
    splitIDArray = chunkIt(idArray, chunkCount)

    count = 0
    collectiveDict = {}
    collectiveArray = []
    for itemArray in splitIDArray:
        string = ','.join(map(str, itemArray))
        #print("http://www.gw2spidy.com/api/v0.9/json/items/*all*/0?filter_ids=" + string)
        try:
            requestItem = requests.get("http://www.gw2spidy.com/api/v0.9/json/items/*all*/0?filter_ids=" + string)
            itemJSON = requestItem.json()
        except json.decoder.JSONDecodeError:
            print("Failed fetching prices from spidy")
            return
        count += 1
        for JSONItem in itemJSON["results"]:
            collectiveArray.append(JSONItem)
            collectiveDict[JSONItem["data_id"]] = JSONItem

    outputFile = open(itemPricePath, "w")
    open(itemPricePath, "w")
    json.dump(collectiveArray, outputFile)
    return
    for item in ShoppingList:
        print(str(counter) + '/' + str(total))
        if ShoppingList[item].id != None:
            itemText =  requests.get("http://www.gw2spidy.com/api/v0.9/json/item/" + str(ShoppingList[item].id)).text
            outputFile.write(itemText)
            if counter != len(ShoppingList):
                outputFile.write(",\n")
            else:
                outputFile.write("\n]")
                break
        counter += 1

def updateItemPrices(ShoppingList):
    os.chdir(os.path.join(os.path.abspath(dir_), "Items"))
    print("Updating price list.  This will take a while")
    counter = 1
    outputFile = open(itemPricePath, "w")
    outputFile.write("[\n")
    total = len(ShoppingList)
    coutner = 1
    for item in ShoppingList:
        #print(str(counter) + '/' + str(total))
        if ShoppingList[item].id != None:
            itemText =  requests.get("http://www.gw2spidy.com/api/v0.9/json/item/" + str(ShoppingList[item].id)).text
            outputFile.write(itemText)
            if counter != len(ShoppingList):
                outputFile.write(",\n")
            else:
                outputFile.write("\n]")
                break
        counter += 1

def calculateTotalCost(itemList, priceList):
    sum = 0
    for item in itemList:
        if item not in priceList:
            eprint(item, " Not in price list!")
        else:
            formatGoldAmount(priceList[item].buyPrice)
            sum += priceList[item].buyPrice * itemList[item].amount
    print(formatGoldAmount(sum))

    return sum

def createItemPriceList():
    os.chdir(os.path.join(os.path.abspath(dir_), "Items"))
    itemFile = open(itemPricePath)
    itemJSON = json.load(itemFile)
    priceList = {}
    for item in itemJSON:
        name = item['name']
        id = item['data_id']
        buyPrice = item['max_offer_unit_price']
        sellPrice = item['min_sale_unit_price']
        priceList[name] = ItemPrice(id, name, buyPrice, sellPrice)
    return priceList

def formatGoldAmount(amount):
    gold = math.floor(amount / 10000)
    silver = math.floor(amount / 100 - gold * 100)
    copper = amount - silver * 100 - gold * 10000
    string = str(gold) + "g " + str(silver) + "s " + str(copper) + "c"
    return string




def makeShoppingList():
    os.chdir(os.path.join(os.path.abspath(dir_), "Database"))
    ignoreList = ["Consumable", "GuildHall", "GuildHallExpedition", "Decoration", "Claimable"]
    list = {}
    tempList = {}
    idList = {}
    tempIDList = {}
    guildUpgradeList = {}
    tempGuildUpgradeList = {}
    guildUpgradeByIDList = {}
    tempGuildUpgradeByIDList = {}
    ignoreIDList = []
    for file in os.listdir():
        if file not in ignoreList:
            tempList, tempIDList, tempGuildUpgradeList, tempGuildUpgradeByIDList = makeShoppingListSingleFile(file)
            list = mergeLists( tempList, list)
            idList = mergeLists(tempIDList, idList)
            guildUpgradeList = mergeLists(tempGuildUpgradeList, guildUpgradeList)
            guildUpgradeByIDList = mergeLists(guildUpgradeByIDList, tempGuildUpgradeByIDList)
        else:
            ignoreIDList =  getIgnoreList(file) + ignoreIDList
    #printShoppingListOrdered(list)
    return list, idList, guildUpgradeList, guildUpgradeByIDList, ignoreIDList

def getIgnoreList(file):
    f = open(file)
    fileJSON = json.load(f)
    ignoreList = []
    for item in fileJSON:
        ignoreList.append(item["id"])
    return ignoreList

def makeShoppingListSingleFile(file):
    f = open(file)
    fileJSON = json.load(f)
    list = {}
    idList = {}
    guildUpgradesList = {}
    gUpgradeItemList = {}
    guildUpgradeByIDList = {}

    for item in fileJSON:
        for costs in item["costs"]:
            if 'item_id' not in costs:
                addItemToHash(list, costs["name"], None, costs["count"], None)
                addItemToHash(gUpgradeItemList, costs["name"], None, costs["count"], None)
            else:
                addItemIDToHash(idList, costs["name"], costs['item_id'], costs["count"], None)
                addItemToHash(list, costs["name"], costs['item_id'], costs["count"], None)
                addItemToHash(gUpgradeItemList, costs["name"], costs['item_id'], costs["count"], None)
        #carefull with this next line, it might cause bugs if guild upgrades are not unique
        guildUpgradesList[item["name"]] = guildUpgrade(item["id"], item["name"], gUpgradeItemList, item["required_level"], item["prerequisites"], item["type"], item["description"], item["experience"])
        guildUpgradeByIDList[item["id"]] = guildUpgrade(item["id"], item["name"], gUpgradeItemList, item["required_level"], item["prerequisites"], item["type"], item["description"], item["experience"])
        gUpgradeItemList = {}
    return list, idList, guildUpgradesList, guildUpgradeByIDList

def printShoppingListOrdered(list):
    newList = {}
    for item in list:
        newList[item] = list[item].amount
    sortedList = sorted(newList.items(), key=operator.itemgetter(1), reverse=True)
    for item in sortedList:
        print(item[0], ": ", item[1])


def printShoppingList(list):
    for item in list:
        test = list[item]
        print(list[item].name, ": ", list[item].amount)

def chunkIt(seq, num):
  avg = len(seq) / float(num)
  out = []
  last = 0.0

  while last < len(seq):
    out.append(seq[int(last):int(last + avg)])
    last += avg

  return out

def mergeLists(list1, list2):
    if list1 == None and list2 == None:
        return {}
    elif list1 != None and list2 == None:
        return list1
    elif list1 == None and list2 != None:
        return list2
    for item in list2:
        if item not in list1:
            list1[item] = list2[item]
        else:
            list1[item].amount += list2[item].amount
    return list1

def merge_two_dicts(x, y):
    """Given two dicts, merge them into a new dict as a shallow copy."""
    z = x.copy()
    z.update(y)
    return z

def addItemIDToHash(hash, itemName, id, amount, img):
    if itemName in hash:
        hash[id].amount = hash[itemName].amount  + amount
    else:
        hash[id] = Item(id, itemName, amount, img)

    return hash

def addItemToHash(hash, itemName, id, amount, img):
    if itemName in hash:
        hash[itemName].amount = hash[itemName].amount  + amount
    else:
        hash[itemName] = Item(id, itemName, amount, img)

    return hash

def addToHash(hash, toBeAdded, value):
    if toBeAdded in hash:
        hash[toBeAdded] = hash[toBeAdded] + value
    else:
        hash[toBeAdded] = value
    return hash

def subtractFromHash(hash, toBeAdded, value):
    if toBeAdded in hash:
        hash[toBeAdded] = hash[toBeAdded] - value
    else:
        hash[toBeAdded] = value * -1
    return hash

def incrementHash(hash, toBeAdded):
    if toBeAdded in hash:
        hash[toBeAdded] += 1
    else:
        hash[toBeAdded] = 1
    return hash

def detectCategories():
    file = open(upgradePath)
    upgradeDB = json.load(file)
    categories = {}
    for element in upgradeDB:
        categories = incrementHash(categories, element["type"])

def is_slice_in_list(s,l):
    return set(s) < set(l) or set(l) < set(s) or set(l) == set(s)

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


if __name__ == '__main__':
    #buildUpgradeDatabaseFromInternetTest()
    main()
    #while True:
        #time.sleep(10)
        #getLogFromInternet()
    #getLogFromInternet()
    #buildUpgradeDatabaseFromInternet()
    #detectCategories()
    #makeShoppingList()