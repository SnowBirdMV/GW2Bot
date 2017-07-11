#! /usr/bin/env python
import discord
from discord.ext import commands
import random
import asyncio
import DatabaseFunctions as db
import pprint
import logging
import datetime
import requests
import wvwFunctions as wvw
import APIKeyHandler as keyHandler
import sys
import os
import zipfile
import datetime


client = discord.Client()

INFOLEVEL = 20

if getattr(sys, 'frozen', False):
    # frozen
    dir_ = os.path.dirname(sys.executable)
else:
    # unfrozen
    dir_ = os.path.dirname(os.path.realpath(__file__))

description = ""
bot = commands.Bot(command_prefix='?', description=description)
shoppingList, itemPrices, upgradeList, treasury, sum, itemPrices, idList, treasuryPerPerson, pricePerPerson, userRetention, favorUpgrades, rawTreasury, ogUserList = db.main()
apiKeyCache = wvw.readAPIKeys()
timerCache = wvw.readTimers()
backupFolders = ["APIKeys", "Database", "guildLogs", "guildProgress", "items", "timers"]
backupPath = os.path.join(dir_, "Backup")

def backupData():
    ziph = zipfile.ZipFile(os.path.join(backupPath, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")) + ".zip", 'w', zipfile.ZIP_DEFLATED)
    path = dir_
    for root, dirs, files in os.walk(path):
        if os.path.basename(root) in backupFolders:
            print(root)
            for file in files:
                ziph.write(os.path.join(root, file))
    ziph.close()

backupData()




@asyncio.coroutine
def my_background_task():
    global shoppingList, itemPrices, upgradeList, treasury, sum, itemPrices, idList, treasuryPerPerson, pricePerPerson, userRetention, favorUpgrades
    shoppingList, itemPrices, upgradeList, treasury, sum, itemPrices, idList, treasuryPerPerson, pricePerPerson, userRetention, favorUpgrades = db.main()
    while(1):
        yield from asyncio.sleep(15)  # task runs every 15 seconds
        shoppingList, itemPrices, upgradeList, treasury, sum, itemPrices, idList, treasuryPerPerson, pricePerPerson, userRetention, favorUpgrades = db.main()

@bot.event
@asyncio.coroutine
def on_message_delete(message):
    pass

@bot.event
@asyncio.coroutine
def on_error(event):
    yield from bot.say("An error has occurred")
    yield from printByNewLine(event)

@bot.command(pass_context=True)
@asyncio.coroutine
def invites(ctx, arg=""):
    global userRetention
    output = db.formatUserRetention()
    yield from printByNewLine(output)

@bot.command(pass_context=True)
@asyncio.coroutine
def rawInvites(ctx, arg=""):
    global userRetention
    output = db.formatUserRetention(raw=True)
    yield from printByNewLine(output)

@bot.command(pass_context=True)
@asyncio.coroutine
def bank(ctx, arg=""):
    global apiKeyCache, treasury, rawTreasury
    senderID = ctx.message.author.id
    key = keyHandler.doesUserHaveKey(apiKeyCache, senderID)
    print(key)
    print(senderID)
    if not key:
        yield from bot.say(
            "An API key is needed to use this command.  You can supply one with the \"?api <API Key>\" command.")
        return
    mats = keyHandler.getUserMaterials(apiKeyCache, ctx.message.author.id)
    if mats == -1:
        yield from bot.say("Something didn't work right, not sure what though >.>")
        return
    neededMats = keyHandler.compareMatsToNeededItems(mats, treasury, idList, rawTreasury)
    test = treasury
    test2 = idList
    output = db.formatItemList(neededMats)
    yield from printByNewLine(output)
    return

@bot.command(pass_context=True, aliases=["W"])
@asyncio.coroutine
def wvwInfo(ctx, arg=""):
    if arg == "":
        yield from bot.say("No argument was given")
        return
    global apiKeyCache
    senderID = ctx.message.author.id
    key = keyHandler.doesUserHaveKey(apiKeyCache, senderID)
    print(key)
    print(senderID)
    if not key:
        yield from bot.say("An API key is needed to use WvW commands.  You can supply one with the \"?api <API Key>\" command.")
        return
    global timerCache
    if arg == "start":
        timerCache = wvw.startTimer(senderID, timerCache, key)
        wvw.writeTimerList(timerCache)
        yield from bot.say("Timer started.")
        print("start")
    elif arg == "check":
        netKilled = wvw.checkTimer(senderID, timerCache, key)
        totalKilled = wvw.checkTotalKills(senderID, timerCache, key)
        if netKilled is not False or netKilled is 0:
            killCountMessage = discord.Embed(colour=0xDEADBF)
            killCountMessage.add_field(name="Killed Since Timer", value=str(netKilled))
            killCountMessage.add_field(name="Total Killed", value=str(totalKilled))
            yield from bot.say("", embed=killCountMessage)
        else:
            yield from bot.say("You have not started your kill count yet, I went ahead and started it for you")
        print("check")
    elif arg == "stop":
        result = wvw.deleteTimer(senderID, timerCache)
        if result:
            yield from bot.say("Stopped your timer")
        else:
            yield from bot.say("You did not have a timer running.")
        print("end")
    else:
        yield from bot.say("Invalid argument \"" + arg + "\", valid arguments are \"start, check, stop\"")
    return

@bot.command()
@asyncio.coroutine
def info():
    killCount = wvw.getInfo()
    if killCount == -1:
        yield from bot.say("could not find kill count")
    else:
        yield from bot.say(killCount)

@bot.command(pass_context=True)
@asyncio.coroutine
def api(ctx, apiKey):
    global apiKeyCache
    keyInfo = requests.get("https://api.guildwars2.com/v2/tokeninfo/?access_token=" + apiKey)
    keyInfoJSON = keyInfo.json()
    try:
        if keyInfoJSON["text"] == "invalid key":
            yield from bot.say("Invalid API key")
            try:

                test = ctx.message
                yield from bot.delete_message(ctx.message)
            except discord.errors.HTTPException:
                yield from bot.say(
                    "I tried to delete your message for security reasons, but I could not because I do not have the required permissions.")
            return
    except KeyError:
        pass

    if ctx.message.author.id in apiKeyCache:
        yield from bot.say("replacing existing API key with the new one.")
    else:
        yield from bot.say("Adding API key.  You will now be able to use the WvW commands.")
    apiKeyCache[ctx.message.author.id] = apiKey
    try:
        yield from bot.delete_message(ctx.message)
    except discord.errors.HTTPException:
        yield from bot.say(
            "I tried to delete your message for security reasons, but I could not because I do not have the required permissions.")
    wvw.writeAPIKeys(apiKeyCache)


@bot.command(pass_context=True)
@asyncio.coroutine
def test(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.message.author

    yield from bot.say('{0} joined at {0.joined_at}'.format(member))


@bot.command()
@asyncio.coroutine
def error():
    number = 0
    test = ""
    test += number

@bot.command()
@asyncio.coroutine
def refresh():
    """Refreshes the guild's data"""
    yield from bot.say("Fetching data...")
    global shoppingList, itemPrices, upgradeList, treasury, sum, itemPrices, idList, treasuryPerPerson, pricePerPerson, userRetention, favorUpgrades, rawTreasury, ogUserList
    shoppingList, itemPrices, upgradeList, treasury, sum, itemPrices, idList, treasuryPerPerson, pricePerPerson, userRetention, favorUpgrades, rawTreasury, ogUserList = db.main()
    yield from bot.say("Re-fetched guild data and item prices.")

@bot.command()
@asyncio.coroutine
def treasuryItem(itemName):
    """Prints treasury info about an item"""
    output = ""
    itemList = db.itemInList(itemName)
    if itemList is None:
        yield from bot.say(itemName + " did not match any item names")
        return
    itemList.sort()
    longestLine = db.findLongestItemName(itemList)
    output += "Name"
    while len(output) < longestLine:
        output += " "
    output += "Amount"
    while len(output) < longestLine + 8:
        output += " "
    output += "Needed\n"
    for item in itemList:
        output += db.formatItemremaining(item, longestLine) + "\n"
    yield from printByNewLine(output)

@bot.command()
@asyncio.coroutine
def TI(itemName):
    output = ""
    itemList = db.itemInList(itemName)
    if itemList is None:
        yield from bot.say(itemName + " did not match any item names")
        return
    itemList.sort()
    longestLine = db.findLongestItemName(itemList)
    output += "Name"
    while len(output) < longestLine:
        output += " "
    output += "Amount"
    while len(output) < longestLine + 8:
        output += " "
    output += "Needed\n"
    for item in itemList:
        output += db.formatItemremaining(item, longestLine) + "\n"
    yield from printByNewLine(output)

@bot.command()
@asyncio.coroutine
def contributors(itemName=None):
    """Prints a breakdown of what a user has contributed"""
    print(itemName)
    debug = itemName
    output = ""
    passed = 0
    if itemName == None:
        yield from bot.say("Usage '?contributors <itemName>'")
        return
    itemList = db.itemInList(itemName)
    if not itemList:
        yield from bot.say("No item found containing '" + itemName + "'")
    else:
        itemList.sort()
        count = 0
        for item in itemList:
            if db.itemInContributors(item):
                passed = 1
                count += 1
                output = item + "\n"
                output += db.formatContributorItem(item)
                yield from printByNewLine(output)
            if count == 4:
                return
    if passed == 0:
        yield from bot.say("No one has contributed '" + itemName + "' to the treasury yet.")


@bot.command()
@asyncio.coroutine
def item(name):
    """Prints the remainder of an item for all upgrades"""
    output = ""
    shoppingList = db.shoppingList
    itemList = db.itemInShoppingList(name)
    if len(itemList) == 0:
        yield from bot.say("No item found containing '" + name + "'")
        return
    itemList.sort()
    test = shoppingList
    print(itemList)
    longestLine = db.findLongestItemName(itemList)
    output = "Item"
    while len(output) < longestLine:
        output += " "
    output += "Amount"
    while len(output) < longestLine + 8:
        output += " "
    output += "Cost\n"
    count = 0
    failed = 0
    if itemList:
        for item in itemList:
            output += db.formatItemCost(shoppingList[item], shoppingList[item].amount, longestLine) + "\n"
    else:
        failed += 1
    if failed == 1:
        yield from bot.say("No item found containing '" + name + "'")
    else:
        yield from printByNewLine(output)

@bot.command()
@asyncio.coroutine
def shoppingList(fullList=None):
    """Prints all items needed to get all of the upgrades"""
    print(fullList)
    if fullList == "full":
        output = db.formatShoppingList(fullList=True) 
    elif fullList == None:
        output = db.formatShoppingList()
    yield from printByNewLine(output)


@bot.event
@asyncio.coroutine
def on_ready():
    print('------')
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command()
@asyncio.coroutine
def wiki(name):
    """Prints a wiki link for anything matching the search"""
    global upgradeList
    upgrade = db.upgradeInList(name)
    itemList = db.itemInList(name)
    count = 0
    failed = 0

    if upgrade and itemList:
        itemList.sort()
        if len(upgrade) + len(itemList) > 4:
            yield from bot.say("More than 4 matches for '" + name + "' only the first 4 matches will be displayed.\n--------------------------------------------------------------------------------")
    if upgrade:
        for item in upgrade:
            if count > 3:
                return
            output = item.name.replace(" ", "_")
            yield from bot.say(item.name + "\n<https://wiki.guildwars2.com/wiki/" + output + ">")
            count += 1
    else:
        failed += 1
    if itemList:
        for item in itemList:
            if count > 3:
                return
            output = item.replace(" ", "_")
            yield from bot.say(item + "\n<https://wiki.guildwars2.com/wiki/" + output + ">")
            count += 1
    else:
        failed += 1

    if failed == 2:
        yield from bot.say("Nothing found containing '" + name + "'")

@bot.command(aliases=["TC"])
@asyncio.coroutine
def treasuryContributors(user=None):
    """Prints a list of treasury donors"""
    print(user)
    debug = user

    if user == None:
        yield from printByNewLine(db.formattreasuryCostByUser())
    else:
        username = db.userInTreasury(user)
        if username:
            yield from printByNewLine(db.formatUserContribution(username))
        else:
            yield from bot.say("no user found containing '" + user + "'")


@bot.command()
@asyncio.coroutine
def refreshItemPrices():
    """Refreshes the item price data"""
    shoppingList = db.shoppingList
    yield from bot.say("Re-fetching price data, this will take about a minute")
    db.updateItemPrices(shoppingList)
    yield from bot.say("Re-fetched price data")

@bot.command()
@asyncio.coroutine
def aetherium():
    """Displays aetherium, favor and guild level"""
    aetherium = db.getAetherium()
    favor = db.getFavor()
    gLevel = db.getLevel()
    yield from printByNewLine("Aetherium: " + str(aetherium) + "\nFavor: " + str(favor) + "\nLevel: " + str(gLevel))

@bot.command(aliases=["CTU"])
@asyncio.coroutine
def cheapestTotalUpgrades():
    """Displays all available upgrades"""
    output = db.formatCheapestUpgradesByTotalCost()
    yield from printByNewLine(output)

@bot.command(aliases=["CCU"])
@asyncio.coroutine
def cheapestCurrentUpgrades():
    """Displays all available upgrades"""
    output = db.formatCheapestUpgradesByCurentCost()
    yield from printByNewLine(output)

@bot.command(aliases=["MU"])
@asyncio.coroutine
def missingUpgrades(upgradeName=None):
    """Displays all of the missing guild upgrades"""
    if upgradeName == None:
        output = db.formatAllUpgradesByCurentCost()
        yield from printByNewLine(output)
        return
    upgrade = db.missingUpgradeInList(upgradeName)
    count = 0
    if upgrade:
        for item in upgrade:
            if count > 3:
                return
            output = db.formatAllUpgradeSearch(item.name)
            yield from printByNewLine(output + "Total cost    Current Cost\n" + db.formatGoldAmount(item.totalPrice) + " | " + db.formatGoldAmount(item.curentPrice))
            count += 1
    else:
        yield from bot.say("no upgrade found containing '" + upgradeName + "'")


@bot.command(aliases=["U"])
@asyncio.coroutine
def upgrade(upgradeName):
    """Displays details about an upgrade"""
    if upgradeName == None:
        bot.say("Comand usage is `?upgrade <upgradeName>`")
    global upgradeList
    upgrade = db.upgradeInList(upgradeName)
    count = 0
    if upgrade:
        for item in upgrade:
            if count > 3:
                return
            output = db.formatNeededUpgradeSearch(item.name)
            yield from printByNewLine(output + "Total cost    Current Cost\n" + db.formatGoldAmount(item.totalPrice) + " | " + db.formatGoldAmount(item.curentPrice))
            count += 1
    else:
        yield from bot.say("no upgrade found containing '" + upgradeName + "'")


@bot.command()
@asyncio.coroutine
def upgrades():
    """Displays detailed info about all current upgrades"""
    yield from printUpgrades(db.formatFavorUpgradesGlobal())

@bot.command(aliases=["UL"])
@asyncio.coroutine
def upgradeList():
    print("Hello")
    yield from printUpgrades(db.formatFavorUpgradesLongGlobal())

#@bot.command()
#@asyncio.coroutine
#def add(left : int, right : int):
#    """Adds two numbers together."""
#    yield from bot.say(left + right)
#
#@bot.command()
#@asyncio.coroutine
#def roll(dice : str):
#    """Rolls a dice in NdN format."""
#    try:
#        rolls, limit = map(int, dice.split('d'))
#    except Exception:
#        yield from bot.say('Format has to be in NdN!')
#        return
#
#    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
#    yield from bot.say(result)
#
#@bot.command(description='For when you wanna settle the score some other way')
#@asyncio.coroutine
#def choose(*choices : str):
#    """Chooses between multiple choices."""
#    yield from bot.say(random.choice(choices))
#
#@bot.command()
#@asyncio.coroutine
#def repeat(times : int, content='repeating...'):
#    """Repeats a message multiple times."""
#    for i in range(times):
#        yield from bot.say(content)
#
#@bot.command()
#@asyncio.coroutine
#def joined(member : discord.Member):
#    """Says when a member joined."""
#    yield from bot.say('{0.name} joined in {0.joined_at}'.format(member))
#
#@bot.group(pass_context=True)
#@asyncio.coroutine
#def cool(ctx):
#    """Says if a user is cool.
#
#    In reality this just checks if a subcommand is being invoked.
#    """
#    if ctx.invoked_subcommand is None:
#        yield from bot.say('No, {0.subcommand_passed} is not cool'.format(ctx))
#
#@cool.command(name='bot')
#@asyncio.coroutine
#def _bot():
#    """Is the bot cool?"""
#    yield from bot.say('Yes, the bot is cool.')

def printUpgrades(stringToPrint):
    print("Hello2")
    totalLength = 0
    niceLine = "```"
    if len(stringToPrint) > 9500:
        niceLine += "Output longer than 10000 characters, this will take a minute.\n"
    lineToAdd = "Upgrade"
    while len(lineToAdd) < 50:
        lineToAdd += " "
    lineToAdd += "Favor   Aetherium\n"
    for line in stringToPrint.splitlines():
        if niceLine == "```":
            niceLine += lineToAdd
        totalLength += len(line)
        if totalLength > 1800:
            niceLine += "```"
            print(len(niceLine))
            yield from bot.say(niceLine)
            niceLine = "```" + line + "\n"
            totalLength = 0
        else:
            niceLine += line + "\n"

    if niceLine != "```":
        niceLine += '```'
        yield from bot.say(niceLine)

@asyncio.coroutine
def printByNewLine(stringToPrint):
    totalLength = 0
    niceLine = "```"
    if len(stringToPrint) > 9500:
        niceLine += "Output longer than 10000 characters, this will take a minute.\n"
    for line in stringToPrint.splitlines():
        totalLength += len(line)
        if totalLength > 1900:
            niceLine += "```"
            yield from bot.say(niceLine)
            niceLine = "```" + line + "\n"
            totalLength = 0
        else:
            niceLine += line + "\n"
    if niceLine != "```":
        niceLine += '```'
        yield from bot.say(niceLine)

@asyncio.coroutine
def printNicely(stringToPrint):
    for chunk in chunks(stringToPrint, 1950):
        printChunk = "```" + chunk + "```"
        yield from bot.say(printChunk)
def chunks(s, n):
    """Produce `n`-character chunks from `s`."""
    for start in range(0, len(s), n):
        yield s[start:start+n]


bot.run('MjgzNzI3ODU1MDQzNzM5NjY5.C45RuA.DvqiMBa8CDkvm_BVt4srXgpKnJk')
