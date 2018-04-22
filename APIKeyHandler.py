import requests
from pprint import pprint
import item
import itemPrice

def doesUserHaveKey(apiKeyCache, user):
    if user in apiKeyCache:
        return apiKeyCache[user]
    return False

def getUserMaterials(apiKeyCache, user):
    key = doesUserHaveKey(apiKeyCache, user)
    if not key:
        return -1
    matInfo = requests.get("https://api.guildwars2.com/v2/account/materials/?access_"
                        "token=" + key)
    matInfoJSON = matInfo.json()
    pprint(matInfo)
    return matInfoJSON

def compareMatsToNeededItems(matList, neededList, idList, rawTreasury):
    haveList = {}
    test = rawTreasury
    for material in matList:
        try:
            matName = idList[material["id"]].name
            if matName in neededList:
                if rawTreasury[matName].totalAmount - rawTreasury[matName].curentAmount > 0 and material["count"] > 0:
                    if material["count"] > rawTreasury[matName].totalAmount - rawTreasury[matName].curentAmount:
                        haveList[matName] = item.Item(material["id"], matName,rawTreasury[matName].totalAmount - rawTreasury[matName].curentAmount, None)
                    else:
                        haveList[matName] = item.Item(material["id"], matName, material["count"], None)

        except KeyError:
            pass
    return haveList

