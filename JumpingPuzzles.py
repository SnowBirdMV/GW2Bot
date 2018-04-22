import random

jpData = {}
jpData["Behem Gauntlet"] = "[&BP0BAAA=]"
jpData["Craze's Folly"] = "[&BPcBAAA=]"
jpData["Crimson Plateau"] = "[&BMYDAAA=]"
jpData["Grendich Gamble"] = "[&BNsDAAA=]"
jpData["Wall Breach Blitz"] = "[&BGEBAAA=]"
jpData["Branded Mine"] = "[&BEsBAAA=]"
jpData["Pig Iron Quarry"] = "[&BBkCAAA=]"
jpData["Chaos Crystal Cavern"] = "[&BOQBAAA=]"
jpData["Loreclaw Expanse"] = "[&BMcDAAA=]"
jpData["Professor Portmatt's Lab"] = "[&BKQBAAA=]"
jpData["Not So Secret"] = "[&BBEHAAA=]"
jpData["Swashbuckler's Cove"] = "[&BHoAAAA=]"
jpData["Fawcett's Bounty"] = "[&BLIAAAA=]"
jpData["Fawcett's Revenge"] = "[&BLIAAAA=]"
jpData["The Collapsed Observatory"] = "[&BBIAAAA=]"
jpData["Demongrub Pits"] = "[&BIwAAAA=]"
jpData["Troll's End"] = "[&BBAEAAA=]"
jpData["Urmaug's Secret"] = "[&BDIEAAA=]"
jpData["Weyandt's Revenge"] = "[&BDMEAAA=]"
jpData["Dark Reverie"] = "[&BDUBAAA=]"
jpData["Morgan's Leap"] = "[&BDUBAAA=]"
jpData["Spekks' Laboratory"] = "[&BGoAAAA=]"
jpData["Spelunker's Delve"] = "[&BP4FAAA=]"
jpData["Goemm's Lab"] = "[&BLIEAAA=]"
jpData["Conundrum Cubed"] = "[&BMgCAAA=]"
jpData["Hidden Garden"] = "[&BNECAAA=]"
jpData["Hexfoundry Unhinged"] = "[&BM0BAAA=]"
jpData["Buried Archives"] = "[&BOQGAAA=]"
jpData["Antre of Adjournment"] = "[&BKoCAAA=]"
jpData["Scavenger's Chasm"] = "[&BKUCAAA=]"
jpData["Vizier's Tower"] = "[&BOECAAA=]"
jpData["Skipping Stones"] = "[&BNAGAAA=]"
jpData["Under New Management"] = "[&BNUGAAA=]"
jpData["Tribulation Caverns"] = "[&BPMEAAA=]"
jpData["Tribulation Rift Scaffolding"] = "[&BPMEAAA=]"
jpData["Shattered Ice Ruins"] = "[&BHwCAAA=]"
jpData["Griffonrook Run"] = "[&BOgAAAA=]"
jpData["King Jalis's Refuge"] = "[&BI4AAAA=]"
jpData["Coddler's Cove"] = "[&BDgCAAA=]"
jpData["Only Zuhl"] = "[&BE4CAAA=]"
jpData["Shaman's Rookery"] = "[&BHcBAAA=]"
jpData["Sapphire Sanctum"] = "[&BC4FAAA=]"
jpData["Emerald Sanctum"] = "[&BDgFAAA=]"
jpData["Garnet Sanctum"] = "[&BBwFAAA=]"
jpData["Obsidian Sanctum"] = "[&BAIHAAA=]"
jpDataList = list(jpData)

randomList = []
randomIndex = len(jpData) - 1

def randomPuzzle():
    global randomIndex, randomList
    repeat = 0
    if randomIndex >= len(jpData) - 1:
        randomList = list(range(0, len(jpData)))
        random.shuffle(randomList)
        randomIndex = 0
        repeat = 1
    randomIndex += 1
    name = jpDataList[randomList[randomIndex]]
    #print("Your jumping puzzle is: " + name + " | " + jpData[name])


    result = random.choice(list(jpData))
    return name, jpData[name], repeat
