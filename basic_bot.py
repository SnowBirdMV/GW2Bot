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
import TimerHandlers as TH
import math
import re
import time
import os
import sys
import threading
import raids
import json
import collections
from copy import deepcopy
import JumpingPuzzles as JPList
import difflib
import base64
from decimal import Decimal

from functools import wraps
import errno
import os
import signal
import itertools


devMode = 0


client = discord.Client()

INFOLEVEL = 20

counter = 0

if getattr(sys, 'frozen', False):
	# frozen
	dir_ = os.path.dirname(sys.executable)
else:
	# unfrozen
	dir_ = os.path.dirname(os.path.realpath(__file__))

fourmPath = os.path.join( os.path.abspath(dir_), "fourms")


if devMode == 1:
	raidChannelID = "349112326315835392"
	description = "I am the dev bot."
else:
	raidChannelID = "349009488776527872"
	description = ""

bot = commands.Bot(command_prefix='?', description=description)
shoppingList, itemPrices, upgradeList, treasury, sum, itemPrices, idList, treasuryPerPerson, pricePerPerson, userRetention, favorUpgrades, rawTreasury, ogUserList, userGoldContributions, listOfOGUsers = db.main()
apiKeyCache = wvw.readAPIKeys()
timerCache = wvw.readTimers()
raffleCache = TH.readRaffle()
userList = TH.readAcceptedUserList()
raidChannel = None

header = "Hello @everyone, " \
			 "Change of plans.  We will doing Vale Guardian and Gorseval again, and hopefully we will get to/kill Sabetha\n" \
			 "***Spirit Vale*** - 9/2/17 9:00pm EDT\n" \
			 "Builds and Rotations - <http://qtfy.eu/builds/>\n" \
			 "DPS Meter - https://www.deltaconnected.com/arcdps/\n" \
			 "Convert EDT to your local time - http://www.thetimezoneconverter.com/\n"

boss1Line = ""

footer = "Please make sure if you are new to watch a guide on these bosses and to PLEASE READ THE RAIDING RULES. \n\n" \
		 "Sign up here: <https://docs.google.com/forms/d/1j37Jcy3DEMK4M2xMpOpwHp1Tej4iBH7fM6h5Gy7cCQ0/viewform>"

raidLine = "people have signed up for the raid so far."
singularRaidLine = "person has signed up for the raid so far."
lastRead = -1
if userList == -1:
	print("Creating new user list")
	TH.updateAcceptedUserList({})
	userList = {}
raidTimer = TH.readRaid()
if raidTimer == -1:
	raidMessage = -1
	print("No raid timer set")
else:
	print("Found raid timer")
	raidMessage = list(raidTimer.values())[0]
	pprint.pprint(raidTimer)

devServer = "283729943521656835"



TOSEssay = "Hello, this is the first time you are using this bot.  Due to recent Terms of Service changes in Discord " \
		   "detailed here: <https://www.reddit.com/r/discordapp/comments/6sq866/the_developer_terms_of_service_have_just_been/>" \
		   " I am now required to inform you of several things this bot does.  \n\nBy continuing to use this bot, you " \
		   "acknowledge and express consent to the storage and use, by this bot, of your **public Discord ID, and" \
		   " public Discord username**.  This is done" \
		   " so that several things such as guild raffles and holding your API key (if you choose to give it) " \
		   "can function.  \n\nThis bot *DOES NOT* Log *ANY* messages you send in this server outside of remembering your API " \
		   "key from the ?API command.\n\n"


bannedRoles = ["Bot Ban"]

oldWorldPopData = []

@asyncio.coroutine
async def check_wvw_pop():
	await bot.wait_until_ready()
	while True:
		worldPopRequest = requests.get("https://api.guildwars2.com/v2/worlds?ids=all")
		worldPopJSON = worldPopRequest.json()
		worldPop2JSON = deepcopy(worldPopJSON)
		#worldPop2JSON[0]["population"] = "Full"
		#worldPop2JSON[1]["population"] = "asdf"

		diffListOld = list(itertools.filterfalse(lambda x: x in worldPop2JSON, worldPopJSON))
		diffListNew = list(itertools.filterfalse(lambda x: x in worldPopJSON, worldPop2JSON))

		# pprint(worldPopJSON)
		if diffListOld != []:
			pprint.pprint(diffListOld)
			pprint.pprint(diffListNew)
		#print("Noting Found")
		await asyncio.sleep(60)



class TimeoutError(Exception):
	pass

def timeoutDec(seconds=10, error_message=os.strerror(errno.ETIME)):
	def decorator(func):
		def _handle_timeout(signum, frame):
			yield from bot.say(error_message)

		def wrapper(*args, **kwargs):
			signal.signal(signal.SIGALRM, _handle_timeout)
			signal.alarm(seconds)
			try:
				result = func(*args, **kwargs)
			finally:
				signal.alarm(0)
			return result

		return wraps(func)(wrapper)

	return decorator

class timeout:
	def __init__(self, seconds=1, error_message='Timeout'):
		self.seconds = seconds
		self.error_message = error_message
	def handle_timeout(self, signum, frame):
		raise TimeoutError(self.error_message)
	def __enter__(self):
		signal.signal(signal.SIGALRM, self.handle_timeout)
		signal.alarm(self.seconds)
	def __exit__(self, type, value, traceback):
		signal.alarm(0)

@bot.command(pass_context=True)
@asyncio.coroutine
async def recipe(ctx, chatLink=""):
	itemID = await chatLinkToID(chatLink)
	output = ""

	idRequest = requests.get("https://api.guildwars2.com/v2/recipes/search?input=" + str(itemID))
	recipeList = idRequest.json()
	noRecipes = False
	if not recipeList:
		print("This item is not used in any recipes.")
		noRecipes = True
	recipeLists = await getRecipesFromAPI(recipeList)
	recipeJSON = recipeLists.json()
	ingredientsList = await getIngredientsFromAPI(itemID)
	ingredientsListItemCodes = []
	ingredientCounts = []
	if ingredientsList != None:
		for item in ingredientsList["ingredients"]:
			ingredientsListItemCodes.append(item["item_id"])
			ingredientCounts.append(item["count"])
		print(ingredientsListItemCodes)
		ingredientItemList = await getItemsInfoFromAPI(ingredientsListItemCodes)
		ingredientItemList = ingredientItemList.json()
		output += "Created By:\n"
		print("Crafted by:")
		count = 0
		for item in ingredientItemList:
			print(str(ingredientCounts[count]) + " " + item["name"])
			output += str(ingredientCounts[count]) + " " + item["name"] + " " + item["chat_link"] + "\n"
			count += 1
		output += "\n\n"
	notCraftable = False
	if ingredientsList == None:
		print("This item is not craftable")
		output += "This item is not craftable\n\n\n"
		notCraftable = True
	else:
		ingredientsListJSON = ingredientsList
	if noRecipes:
		output += "\nThis item is used in no recipes."
		await printByNewLine(output)
		return
	itemIDs = []
	for recipe in recipeJSON:
		itemIDs.append(recipe["output_item_id"])
	itemRequest = await getItemsInfoFromAPI(itemIDs)
	itemsJSON = itemRequest.json()
	for item in itemsJSON:
		print(item["name"])
		output += item["name"] + "\n"
		try:
			output += item["description"] + "\n"
			print(item["description"])
		except KeyError:
			output += "No Description\n"
			print("No Description")
		print(item["chat_link"])
		output += item["chat_link"] + "\n\n"
	print(itemIDs)
	await printByNewLine(output)
	print("test")
	return


@asyncio.coroutine
async def getIngredientsFromAPI(itemID):
	idRequest = requests.get("https://api.guildwars2.com/v2/recipes/search?output=" + str(itemID))
	recipeList = idRequest.json()
	if len(recipeList) == 0:
		return None
	return requests.get("https://api.guildwars2.com/v2/recipes/" + str(recipeList[0])).json()

@asyncio.coroutine
async def getItemsInfoFromAPI(itemList):
	itemString = await listToCSV(itemList)
	return requests.get("https://api.guildwars2.com/v2/items?ids=" + itemString)

@asyncio.coroutine
async def getRecipesFromAPI(recipeList):
	recipeString = await listToCSV(recipeList)
	return requests.get("https://api.guildwars2.com/v2/recipes?ids=" + recipeString)

@asyncio.coroutine
async def listToCSV(inputList):
	return ','.join(map(str, inputList))

@asyncio.coroutine
async def chatLinkToID(itemCode):
	itemCode = itemCode[2:-1]
	test = 0
	test = base64.b64decode(itemCode)
	for item in test:
		print(item)
	values = []
	values.append(hex(test[2]))
	values.append(hex(test[3]))
	values.append(hex(test[4]))
	testVal = '0x' + ''.join([format(int(c, 16), '02X') for c in reversed(values)])
	print(testVal)
	itemID = str(int(testVal, 16))
	print(itemID)
	return itemID

@asyncio.coroutine
async def getItemCache():
	itemIDRequest = requests.get("https://api.guildwars2.com/v2/items/")
	itemsIDList = itemIDRequest.json()
	with open("itemDatabase", "r+") as file:
		json.dump(itemsIDList, file)
		#TODO: 300 may be a magic number?
	idMetaList = list(chunks(itemsIDList, math.ceil(len(itemsIDList) / 300)))
	totalItemList = []
	count = 1
	for item in idMetaList:
		while True:
			try:
				itemRequest = requests.get("https://api.guildwars2.com/v2/items?ids=" + listToCSV(item))
				print(str(count) + "/" + str(len(idMetaList)))
				itemRequestJSON = itemRequest.json()
				print(str(len(itemRequestJSON)))
				totalItemList += itemRequestJSON
				count += 1
				break
			except requests.exceptions.ConnectionError:
				print("Connection error, retrying atfer 5 seconds.")
				time.sleep(5)

		#time.sleep(5)
	itemDict = {}
	for item in totalItemList:
		itemDict[item["name"]] = item
	with open("itemDatabase", "w+") as file:
		json.dump(itemDict, file)
	with open("itemDatabase", "r") as file:
		test = json.load(file)
	print("Hello")



@bot.command(pass_context=True)
@asyncio.coroutine
async def age(ctx, userName=""):
	if userName == "":
		await bot.say("Incorrect command usage.  Proper usage is \"?age <UserName>\"")
	global listOfOGUsers
	test = listOfOGUsers
	userNames = list(listOfOGUsers.keys())
	result = difflib.get_close_matches(userName, userNames, cutoff=.4)
	resultList = []
	for name in userNames:
		if userName.lower() in name.lower():
			resultList.append(name)
	resultList = sorted(resultList)
	dateList = []
	timeList = []
	for name in resultList:
		dateTimeList = listOfOGUsers[name].dateAdded.split("T")
		dateList.append(dateTimeList[0])
		timeList.append(dateTimeList[1][:-1])



	header = ["Name", "Date", "Time"]
	contents = []
	contents.append(resultList)
	contents.append(dateList)
	contents.append(timeList)
	output = await makeOuptutTable(header, contents)
	await printByNewLine(output)
	test = result

async def makeOuptutTable(headers, contents, spacing=2):
	if len(headers) != len(contents):
		raise "length of headers is not length of contents headers: " + str(len(headers)) + " contents: " + str(len(contents))

	outputString = ""
	longestLine = []
	for header in headers:
		longestLine.append(len(header))
	counter = 0
	for content in contents:
		for line in content:
			lineLen = len(line)
			if lineLen > longestLine[counter]:
				longestLine[counter] = lineLen
		counter += 1

	for counter in  range(len(longestLine)):
		longestLine[counter] += spacing

	counter = 0
	for header in headers:
		if counter == len(headers) - 1:
			outputString += header
			counter += 1
		else:
			outputString += header + " " * (longestLine[counter] - len(header))
			counter += 1
	outputString += "\n"

	for counter in range(len(contents[0])):
		lengthCounter = 0
		for content in contents:
			if lengthCounter == len(contents) - 1:
				outputString += content[counter]
			else:
				outputString += content[counter] + " " * (longestLine[lengthCounter] - len(content[counter]))
				lengthCounter += 1
		outputString += "\n"

	return outputString

#TODO: make these async functions?
def startFourmServer():
	os.system("python3 " + os.path.join(dir_, "test.py"))
	pass

t = threading.Thread(target=startFourmServer,name="gw2bot_flask_server",)
t.daemon = True
t.start()

def ditermineRaidLoadout(raidData, responseFileName):
	formPath = os.path.join(os.path.join("fourms"), responseFileName)
	formFile = open(formPath)
	form = json.load(formFile)
	for responce in form:
		userName = responce["Username"]
		rawRoles = responce["Roles"]
		roles = rawRoles.split(",")
		try:
			rawSpecialRoles = responce["Special Roles"]
			specialRoles = rawSpecialRoles.split(",")
			roles.extend(specialRoles)
		except KeyError:
			pass
		roles.reverse()
		isExperiencedRaw = responce["Have you finished any of this wings bosses before?"]
		if isExperiencedRaw == "Yes":
			isExperienced = True
		else:
			isExperienced = False
		print(roles)
		for bossName in raidData:
			raidData[bossName], errors = placeUserInBoss(raidData[bossName], roles, userName, isExperienced)
			if errors == True:
				print("Could not place " + userName + " in boss " + bossName)
		test = responce
		print(test)
	return generateRaidMessage(raidData)

def placeUserInBoss(positionList, userRoles, userName, isExperienced):
	errors = False
	for role in userRoles:
		if role in positionList:
			count = 0
			for user in positionList[role]:
				if user == None:
					if isExperienced:
						positionList[role][count] = userName + "(exp)"
					else:
						positionList[role][count] = userName
					return positionList, errors
				count += 1
	errors = True
	return positionList, errors

def generateRaidMessage(raidData):
	global boss1Line
	output = ""
	counter = 1
	for bossName in raidData:
		output += "```css\n"
		output += bossName + ":\n"
		for roleName in raidData[bossName]:
			output += roleName + ": "
			count = 0
			for position in raidData[bossName][roleName]:
				count += 1
				if position == None:
					output += "[Open]"
				else:
					output += position
				if count != len(raidData[bossName][roleName]):
					output += ","
				else:
					output += "\n"
		output += "```"
		if counter == 1:
			output += boss1Line
		counter += 1
	print(output)
	return output


async def checkFourm():
	await bot.wait_until_ready()
	global counter, fourmPath, raidTimer, raidMessage, raidChannel, raidLine, singularRaidLine, lastRead
	await asyncio.sleep(2)

	foundMyMessage = 0
	lastRead = -1
	print(raidChannel)
	print(raidMessage)
	try:
		message = await bot.get_message(raidChannel, raidMessage)
	except discord.errors.NotFound:
		print("Raid message was not found.  Deleting raid timer.")
		raidTimer = -1
		raidMessage = -1
		message = -1
		TH.deleteRaidTimer()
	except discord.errors.HTTPException:
		raidTimer = -1
		raidMessage = -1
		message = -1

	if not message and raidMessage != -1:
		await bot.send_message(raidChannel, raidLine)
		async for message in bot.logs_from(raidChannel, limit=1):
			botMessage = message


	lastRead = -1
	while True:
		if message == -1 and raidTimer != -1 and raidMessage != -1:
			try:
				message = await bot.get_message(raidChannel, raidMessage)
			except discord.errors.NotFound:
				print("Raid message was not found.")
		elif raidTimer != -1 and os.path.isfile(os.path.join(fourmPath, str(list(raidTimer.keys())[0]))) :
			try:
				botMessage = await bot.get_message(raidChannel, list(raidTimer.values())[0])
				if not botMessage and raidMessage != -1:
					await bot.send_message(raidChannel, raidLine)
					async for message in bot.logs_from(raidChannel, limit=1):
						botMessage = message
					TH.saveRaidTimer()
				raidCount = TH.readSpecificRaidTimer(list(raidTimer.keys())[0])
				if lastRead != raidCount:
					if raidCount == 1:
						newMessage = singularRaidLine
					else:
						newMessage = raidLine
					await bot.edit_message(botMessage, str(raidCount) + " " + newMessage)
					lastRead = raidCount
					print("New raid response, total is now: " + str(raidCount))
			except discord.errors.NotFound:
				print("Raid message was not found.  Deleting raid timer.")
				raidTimer = -1
				raidMessage = -1
				message = -1
				TH.deleteRaidTimer()
			except discord.errors.HTTPException:
				raidTimer = -1
				raidMessage = -1
				message = -1

		await asyncio.sleep(4)

async def checkFourmComplex():
	await bot.wait_until_ready()
	global counter, fourmPath, raidTimer, raidMessage, raidChannel, raidLine, singularRaidLine, lastRead, header, boss1Line, footer
	await asyncio.sleep(2)
	raidData = raids.generateRaidData()
	curentRaidBase = raidData[0]



	foundMyMessage = 0
	lastRead = -1
	print(raidChannel)
	print(raidMessage)
	try:
		message = await bot.get_message(raidChannel, raidMessage)
	except discord.errors.NotFound:
		print("Raid message was not found.  Deleting raid timer.")
		raidTimer = -1
		raidMessage = -1
		message = -1
		TH.deleteRaidTimer()
	except discord.errors.HTTPException:
		raidTimer = -1
		raidMessage = -1
		message = -1

	if not message and raidMessage != -1:
		await bot.send_message(raidChannel, raidLine)
		async for message in bot.logs_from(raidChannel, limit=1):
			botMessage = message


	lastRead = -1
	while True:
		if message == -1 and raidTimer != -1 and raidMessage != -1:
			try:
				message = await bot.get_message(raidChannel, raidMessage)
			except discord.errors.NotFound:
				print("Raid message was not found.")
		elif raidTimer != -1 and os.path.isfile(os.path.join(fourmPath, str(list(raidTimer.keys())[0]))) and os.path.isfile(os.path.join(fourmPath, str(list(raidTimer.keys())[0]) + ".responses")) :
			try:
				botMessage = await bot.get_message(raidChannel, list(raidTimer.values())[0])
				if not botMessage and raidMessage != -1:
					await bot.send_message(raidChannel, raidLine)
					async for message in bot.logs_from(raidChannel, limit=1):
						botMessage = message
					TH.saveRaidTimer()
				raidCount = TH.readSpecificRaidTimer(list(raidTimer.keys())[0])
				raidData = TH.readSpecificRaidTimerData(list(raidTimer.keys())[0])
				if lastRead != raidCount:
					newMessage = header
					newRaidBase = deepcopy(curentRaidBase)
					newMessage += ditermineRaidLoadout(newRaidBase, os.path.join(fourmPath, os.path.join(fourmPath, str(list(raidTimer.keys())[0]) + ".responses")))
					newMessage += footer

					await bot.edit_message(botMessage, newMessage)
					#await bot.edit_message(botMessage, str(raidCount) + " " + newMessage)
					lastRead = raidCount
					print("New raid response, total is now: " + str(raidCount))
			except discord.errors.NotFound:
				print("Raid message was not found.  Deleting raid timer.")
				raidTimer = -1
				raidMessage = -1
				message = -1
				TH.deleteRaidTimer()
			except discord.errors.HTTPException:
				raidTimer = -1
				raidMessage = -1
				message = -1

		await asyncio.sleep(4)




@bot.command(pass_context=True, aliases=["jp", "Jp", "jP"])
@asyncio.coroutine
async def JP(ctx):
	name, value, repeat = JPList.randomPuzzle()
	message = ""
	message += "Your jumping puzzle is: " + str(name) + " | " + str(value)
	await bot.say(message)

@bot.command(pass_context=True)
@asyncio.coroutine
async def raid(ctx, arg=""):
	global raidMessage, raidChannel, header
	if arg == "":
		await bot.say("You need to specify a google form ID, example of proper usage:\n```?raid 1FAIpQLSexF8Ofq6t9h4DYjW-IEQUAxKL3Iy9ztNQWuhhhgGgLYAn7CQ```")
		return
	global raidTimer, lastRead

	await bot.send_message(raidChannel, header + raidLine)
	async for message in bot.logs_from(raidChannel, limit=1):
		myMessage = message
	raidTimerDict = {}
	raidTimerDict[arg] = myMessage.id
	TH.saveRaidTimer(raidTimerDict)
	raidTimer = raidTimerDict
	lastRead = -1
	await bot.say("Raid timer set")

@asyncio.coroutine
async def my_background_task():
	await bot.wait_until_ready()
	global shoppingList, itemPrices, upgradeList, treasury, sum, itemPrices, idList, treasuryPerPerson, pricePerPerson, userRetention, favorUpgrades
	while(1):
		await asyncio.sleep(600)  # task runs every 15 seconds
		await bot.change_presence(game=discord.Game(name="Updating API Information."), status="dnd")
		shoppingList, itemPrices, upgradeList, treasury, sum, itemPrices, idList, treasuryPerPerson, pricePerPerson, userRetention, favorUpgrades, rawTreasury, ogUserList, userGoldContributions = db.main()
		await bot.change_presence(game=None, status="online")

@bot.event
async def on_message(message):
	global bannedRoles, userList, TOSEssay, devMode, devServer
	# do some extra stuff here
	test = message

	if devMode == 1:
		if message.server.id != devServer:
			return
	else:
		if message.server.id == devServer:
			return

	if message.author.id == '283727855043739669':
		return
	for role in message.author.roles:
		if role.name in bannedRoles:
			print("found banned role in user's roles")
			return
	test = re.match('\?[a-zA-Z]', message.clean_content)
	if message.author.id not in userList and re.match('\?[a-zA-Z]', message.clean_content):
		userList[message.author.id] = 1
		await bot.send_message(message.channel, content=TOSEssay)
		TH.updateAcceptedUserList(userList)
		return
	await bot.process_commands(message)

@bot.event
async def on_member_join(member):
	#await client.send_message(client.get_channel('283729943521656835'), "THIS IS A TEST")
	pass

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
async def test2(ctx, arg=""):
	global counter
	raidLine = "people have signed up for the raid so far."
	singularRaidLine = "person has signed up for the raid so far."
	raidChannel = bot.get_channel(raidChannelID)
	foundMyMessage = 0
	async for message in bot.logs_from(raidChannel, limit=1000):
		print(message.content)
		if message.author.id == bot.user.id:
			if not message.content.endswith(raidLine) and not message.content.endswith(singularRaidLine):
				pass
			else:
				foundMyMessage = 1
				if counter == 1:
					newMessage = singularRaidLine
				else:
					newMessage = raidLine
				await bot.edit_message(message, str(counter) + " " + newMessage)
				counter += 1
	if foundMyMessage == 0:
		await bot.send_message(raidChannel, raidLine)

@bot.command(pass_context=True)
@asyncio.coroutine
async def test1(ctx, arg=""):
	for line in open("fourm", "r"):
		fourmCount = line
	test = bot.get_channel("275910744753569793")
	await bot.send_message(bot.get_channel('311982878475026432'), str(fourmCount) + " people have signed up for the raid so far")
	print("Hi")

@bot.command(pass_context=True)
@asyncio.coroutine
def raffle(ctx, arg=""):
	global raffleCache, userGoldContributions
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
		TH.createRaffleTimer(userGoldContributions)
		yield from bot.say("Raffle started.")
		pprint.pprint(raffleCache)
		print("start")
	elif arg == "check":
		raffleCache = TH.readRaffle()
		if raffleCache == -1:
			yield from bot.say("No raffle is currently happening")
			return

		rafflePointList = {}
		for user in userGoldContributions:
			print(str(raffleCache[user]) + " " + str(userGoldContributions[user]) + " " + str(
				abs(raffleCache[user] - userGoldContributions[user])))
			rafflePointList[user] = abs(raffleCache[user] - userGoldContributions[user])

		for user in rafflePointList:
			rafflePointList[user] = math.floor(rafflePointList[user] / 5000)
		pprint.pprint(rafflePointList)
		output = db.formatRaffleAChances(rafflePointList)
		yield from printByNewLine(output)
		print("check")
	elif arg == "stop":
		raffleCache = TH.readRaffle()
		if raffleCache == -1:
			yield from bot.say("No raffle is currently happening")
			return

		rafflePointList = {}
		for user in userGoldContributions:
			print(str(raffleCache[user]) + " " + str(userGoldContributions[user]) + " " + str(abs(raffleCache[user] - userGoldContributions[user])))
			rafflePointList[user] = abs(raffleCache[user] - userGoldContributions[user])

		for user in rafflePointList:
			rafflePointList[user] = math.floor(rafflePointList[user] / 5000)
		pprint.pprint(rafflePointList)
		print("end")
	else:
		yield from bot.say("Invalid argument \"" + arg + "\", valid arguments are \"start, check, stop\"")
	return

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


#@bot.command(pass_context=True)
#@asyncio.coroutine
#def test(ctx, member: discord.Member = None):
#    if member is None:
#        member = ctx.message.author
#
#    yield from bot.say('{0} joined at {0.joined_at}'.format(member))


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
	try:
		with timeout(seconds=30):
			yield from bot.say("Fetching data...")
			global shoppingList, itemPrices, upgradeList, treasury, sum, itemPrices, idList, treasuryPerPerson, pricePerPerson, userRetention, favorUpgrades, rawTreasury, ogUserList, userGoldContributions, listOfOGUsers
			yield from bot.change_presence(game=discord.Game(name="Updating API Information."), status="dnd")
			shoppingList, itemPrices, upgradeList, treasury, sum, itemPrices, idList, treasuryPerPerson, pricePerPerson, userRetention, favorUpgrades, rawTreasury, ogUserList, userGoldContributions, listOfOGUsers = db.main()
			yield from bot.change_presence(game=None, status="online")
			#bot.change_presence(status=discord.Status.online)
			yield from bot.say("Re-fetched guild data and item prices.")
	except Exception as e:
		if type(e).__name__ == "TimeoutError":
			yield from bot.say("The refresh command timed out, please try again")
		else:
			yield from bot.say("Failed the refresh command because\n" + "```python\n" + str(e) + "```")
		yield from bot.change_presence(game=None, status="online")


@bot.command(aliases=["TI"])
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
async def on_ready():
	global raidChannel, raidChannelID
	raidChannel = bot.get_channel(raidChannelID)
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


@bot.command(aliases=["U"], pass_context=True)
@asyncio.coroutine
def upgrade(ctx, upgradeName):
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
			link = item.name.replace(" ", "_")
			wikiLink = "https://wiki.guildwars2.com/wiki/" + link
			print(wikiLink)
			messageEmbed = discord.Embed(title=item.name,
										 url=wikiLink)
			yield from printByNewLine(output + "Total cost    Current Cost\n" + db.formatGoldAmount(item.totalPrice) + " | " + db.formatGoldAmount(item.curentPrice), embed=messageEmbed, ctx=ctx)
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

@bot.command(aliases=["rd", "Rd", "rD", "RD", "Rolldisadvantage", "rolldisadvantage", "RollDisadvantage"], pass_context=True)
@asyncio.coroutine
def rollDisadvantage(ctx, dice : str):
	"""Rolls a dice in NdN format with disadvantage."""
	pastaFlag = False
	if ctx.message.author.id == "235507199022071809":
		pass
		#pastaFlag = True

	resultDict = yield from rollLogic(dice)

	rollList = resultDict["rollList"]
	subTotal = resultDict["subTotal"]
	critFail = resultDict["critFail"]
	critSuccess = resultDict["critSuccess"]
	total = resultDict["total"]
	average = resultDict["average"]
	modType = resultDict["modType"]
	mod = resultDict["mod"]

	result = ""
	lowest = min(rollList)
	rawLowest = lowest
	if modType == "-":
		lowest -= mod
	elif modType == "+":
		lowest += mod

	result += "**" + str(lowest) + "**\n"
	result += "`"
	result += ', '.join(str(x) for x in rollList)
	result += " [" + str(subTotal) + "]` average: " + str(round(Decimal(average), 2)) + " lowest: " + str(rawLowest) + "\n"


	if critFail or critSuccess:
		if critSuccess:
			result += str(critSuccess) + " Crit Successes\n"
		if critFail:
			result += str(critFail) + " Crit Fails\n"
	yield from bot.say(result)

@bot.command(aliases=["ra", "Ra", "rA", "RA", "RollAdvantage", "rolladvantage", "Rolladvantage"], pass_context=True)
@asyncio.coroutine
def rollAdvantage(ctx, dice : str):
	"""Rolls a dice in NdN format with advantage."""
	pastaFlag = False
	if ctx.message.author.id == "235507199022071809":
		pass
		#pastaFlag = True

	resultDict = yield from rollLogic(dice)

	rollList = resultDict["rollList"]
	subTotal = resultDict["subTotal"]
	critFail = resultDict["critFail"]
	critSuccess = resultDict["critSuccess"]
	total = resultDict["total"]
	average = resultDict["average"]
	modType = resultDict["modType"]
	mod = resultDict["mod"]

	result = ""
	highest = max(rollList)
	rawHighest = highest
	if modType == "-":
		highest -= mod
	elif modType == "+":
		highest += mod

	result += "**" + str(highest) + "**\n"
	result += "`"
	result += ', '.join(str(x) for x in rollList)
	result += " [" + str(subTotal) + "]` average: " + str(round(Decimal(average), 2)) + " highest: " + str(rawHighest) + "\n"


	if critFail or critSuccess:
		if critSuccess:
			result += str(critSuccess) + " Crit Successes\n"
		if critFail:
			result += str(critFail) + " Crit Fails\n"
	yield from bot.say(result)

@bot.command(aliases=["r", "R"], pass_context=True)
@asyncio.coroutine
def roll(ctx, dice : str):
	"""Rolls a dice in NdN format."""
	pastaFlag = False
	if ctx.message.author.id == "235507199022071809":
		pass
		#pastaFlag = True

	resultDict = yield from rollLogic(dice)

	rollList = resultDict["rollList"]
	subTotal = resultDict["subTotal"]
	critFail = resultDict["critFail"]
	critSuccess = resultDict["critSuccess"]
	total = resultDict["total"]
	average = resultDict["average"]
	modType = resultDict["modType"]
	mod = resultDict["mod"]

	result = ""
	result += "**" + str(total) + "**\n"
	result += "`"
	result += ', '.join(str(x) for x in rollList)
	result += " [" + str(subTotal) + "]` average: " + str(round(Decimal(average), 2)) + "\n"


	if critFail or critSuccess:
		if critSuccess:
			result += str(critSuccess) + " Crit Successes\n"
		if critFail:
			result += str(critFail) + " Crit Fails\n"
	yield from bot.say(result)

@asyncio.coroutine
def rollLogic(dice, pastaFlag=False):
	hasMod = False
	modType = ""
	total = 0
	mod = None

	try:
		dice = dice.lower()
		rolls, rightHalf = map(str, dice.split('d'))
		rolls = int(rolls)
	except:
		try:
			if dice[0] == "d":
				rightHalf = dice[1:]
				rolls = 1
			else:
				raise Exception 
		except:
			yield from bot.say("Format has to be NdN")
			return


	try:
		limit, mod = map(int, rightHalf.split('+'))
		hasMod = True
		modType = "+"

	except Exception as e:
		#yield from bot.say("```python\n1: " +  str(e) + "```")
		try:
			limit, mod = map(int, rightHalf.split('-'))
			hasMod = True
			modType = "-"
		except Exception as e:
			#yield from bot.say("```python\n2: " +  str(e) + "```")
			#yield from bot.say("invalid modifier, needs to be '+' or '-'")
			limit = int(rightHalf)


	critFail = 0
	critSuccess = 0
	rollList = []
	total = 0
	subTotal = 0
	for roll in range(rolls):
		roll = random.randint(1, limit)
		if pastaFlag:
			roll = 1
		if roll == 1:
			critFail += 1
		elif roll == limit:
			critSuccess += 1
		rollList.append(roll)
		subTotal += roll

	if hasMod:
		if modType == "+":
			total = subTotal + mod
		elif modType == "-":
			total = subTotal- mod
		
	else:
		total = subTotal

	average = subTotal / rolls

	returnDict = {}
	returnDict["rollList"] = rollList
	returnDict["subTotal"] = subTotal
	returnDict["critFail"] = critFail
	returnDict["critSuccess"] = critSuccess
	returnDict["total"] = total
	returnDict["average"] = average
	returnDict["modType"] = modType
	returnDict["mod"] = mod


	return returnDict

	result = ""

	result += "**" + str(total) + "**\n"
	result += "`"
	result += ', '.join(str(x) for x in rollList)
	result += " [" + str(subTotal) + "]` average: " + str(round(Decimal(average), 2)) + "\n"


	if critFail or critSuccess:
		if critSuccess:
			result += str(critSuccess) + " Crit Successes\n"
		if critFail:
			result += str(critFail) + " Crit Fails\n"
	yield from bot.say(result)
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
def printByNewLine(stringToPrint, embed=None, ctx=None):
	if not embed and not ctx:
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

	if embed and ctx:
		totalLength = 0
		niceLine = "```"
		if len(stringToPrint) > 9500:
			niceLine += "Output longer than 10000 characters, this will take a minute.\n"
		for line in stringToPrint.splitlines():
			totalLength += len(line)
			if totalLength > 1900:
				niceLine += "```"
				embed.description = niceLine
				yield from bot.send_message(ctx.message.channel, embed=embed)
				niceLine = "```" + line + "\n"
				totalLength = 0
			else:
				niceLine += line + "\n"
		if niceLine != "```":
			niceLine += '```'
			embed.description = niceLine
			yield from bot.send_message(ctx.message.channel, embed=embed)



@asyncio.coroutine
def printNicely(stringToPrint):
	for chunk in chunks(stringToPrint, 1950):
		printChunk = "```" + chunk + "```"
		yield from bot.say(printChunk)
def chunks(s, n):
	"""Produce `n`-character chunks from `s`."""
	for start in range(0, len(s), n):
		yield s[start:start+n]

if devMode == 0:
	bot.loop.create_task(checkFourmComplex())
else:
	bot.loop.create_task(checkFourmComplex())


#bot.loop.create_task(my_background_task())
#bot.loop.create_task(check_wvw_pop())
bot.run('MjgzNzI3ODU1MDQzNzM5NjY5.C45RuA.DvqiMBa8CDkvm_BVt4srXgpKnJk')
