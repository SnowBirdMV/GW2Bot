import os
import sys
import json
import collections

if getattr(sys, 'frozen', False):
    # frozen
    dir_ = os.path.dirname(sys.executable)
else:
    # unfrozen
    dir_ = os.path.dirname(os.path.realpath(__file__))

def generateRaidData():
    wings = [None, None, None, None]

    w1Bosses = collections.OrderedDict()
    w1Bosses["Vale"] = collections.OrderedDict()
    w1Bosses["Vale"]["DPS"] = [None, None, None, None]
    w1Bosses["Vale"]["PS"] = [None, None]
    w1Bosses["Vale"]["Druid"] = [None, None]
    w1Bosses["Vale"]["Chrono"] = [None]
    w1Bosses["Vale"]["Chrono Tank"] = [None]

    w1Bosses["Gorseval"] = collections.OrderedDict()
    w1Bosses["Gorseval"]["DPS"] = [None, None, None, None]
    w1Bosses["Gorseval"]["PS"] = [None, None]
    w1Bosses["Gorseval"]["Druid"] = [None, None]
    w1Bosses["Gorseval"]["Chrono"] = [None]
    w1Bosses["Gorseval"]["Chrono Tank"] = [None]

    w1Bosses["Sabetha"] = collections.OrderedDict()
    w1Bosses["Sabetha"]["DPS"] = [None, None, None, None]
    w1Bosses["Sabetha"]["PS"] = [None, None]
    w1Bosses["Sabetha"]["Druid"] = [None, None]
    w1Bosses["Sabetha"]["Chrono"] = [None, None]

    wings[0] = w1Bosses

    w2Bosses = collections.OrderedDict()
    w2Bosses["Slothasor"] = collections.OrderedDict()
    w2Bosses["Slothasor"]["DPS"] = [None, None, None, None]
    w2Bosses["Slothasor"]["PS"] = [None, None]
    w2Bosses["Slothasor"]["Druid"] = [None, None]
    w2Bosses["Slothasor"]["Chrono"] = [None, None]

    w2Bosses["the Bandit Trio"] = collections.OrderedDict()
    w2Bosses["the Bandit Trio"]["DPS"] = [None, None, None, None]
    w2Bosses["the Bandit Trio"]["PS"] = [None, None]
    w2Bosses["the Bandit Trio"]["Druid"] = [None, None]
    w2Bosses["the Bandit Trio"]["Chrono"] = [None, None]

    w2Bosses["Matthias Gabrel"] = collections.OrderedDict()
    w2Bosses["Matthias Gabrel"]["DPS"] = [None, None, None, None]
    w2Bosses["Matthias Gabrel"]["PS"] = [None, None]
    w2Bosses["Matthias Gabrel"]["Druid"] = [None, None]
    w2Bosses["Matthias Gabrel"]["Chrono"] = [None]
    w2Bosses["Matthias Gabrel"]["Auramancer"] = [None]

    wings[1] = w2Bosses
    wings[2] = w1Bosses



    w4Bosses = collections.OrderedDict()
    w4Bosses["Cairn"] = collections.OrderedDict()
    w4Bosses["Cairn"]["DPS"] = [None, None, None, None]
    w4Bosses["Cairn"]["PS"] = [None, None]
    w4Bosses["Cairn"]["Druid"] = [None, None]
    w4Bosses["Cairn"]["Chrono"] = [None, None]

    w4Bosses["MO"] = collections.OrderedDict()
    w4Bosses["MO"]["DPS"] = [None, None, None, None]
    w4Bosses["MO"]["PS"] = [None, None]
    w4Bosses["MO"]["Druid"] = [None, None]
    w4Bosses["MO"]["Chrono"] = [None, None]

    w4Bosses["Samarog"] = collections.OrderedDict()
    w4Bosses["Samarog"]["DPS"] = [None, None, None, None]
    w4Bosses["Samarog"]["PS"] = [None, None]
    w4Bosses["Samarog"]["Druid"] = [None, None]
    w4Bosses["Samarog"]["Chrono"] = [None, None]

    wings[3] = w4Bosses

    return wings

def ditermineRaidLoadout(raidData, formPath):
    formFile = open(formPath)
    form = json.load(formFile)
    for responce in form:
        userName = responce["Username"]
        rawRoles = responce["Roles"]
        roles = rawRoles.split(",")
        rawSpecialRoles = responce["Special Roles"]
        specialRoles = rawSpecialRoles.split(",")
        roles.extend(specialRoles)
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
    errors = True
    return positionList, errors

def generateRaidMessage(raidData, raidLocation):
    output = ""
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
    print(output)
    return output