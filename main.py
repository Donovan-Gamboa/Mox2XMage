import argparse
from tokenize import String
import requests
import random
import json
import logging
import os
import re
import html
from bs4 import BeautifulSoup   #https://www.crummy.com/software/BeautifulSoup/bs4/doc/#navigating-the-tree
from copy import deepcopy


user_agent_list = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
    'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0; Trident/5.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0; MDDCJS)',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)',
]

def debug(args):  # Enable debugging printing
    print("debug")

def printJson(j):
    print(json.dumps(j, indent=4))


def logResponse(name, r):  # Logs the request to a .html file for reviewing
    f = open(name, "w")
    text = str(r.status_code) + "\n" + \
        str(r.headers) + "\n\n\n\n" + str(r.text)
    text = text.replace("', '", "',\n'")
    f.write(text)
    f.close()

DeckListTemplate = {  # Remember to deepcopy() when copying this template
    "format": "",       # Format
    "companions": [],   # List of <CardFormatTemplate>
    "commanders": [],   # List of <CardFormatTemplate>
    "mainboard": [],    # List of <CardFormatTemplate>
    "sideboard": []     # List of <CardFormatTemplate>
}
CardFormatTemplate = {
    "quantity": 0,
    "name": "",         # Lightning Bolt
    "set": "",          # M12
    "setNr": "1",       # 65
}

def convertDeckToXmage(deckList):
    # If the format is EDH, make the Commander the only sideboard card
    if deckList["format"] == "commander":
        deckList["sideboard"] = []
        for cmdr in deckList["commanders"]:
            deckList["sideboard"].append(cmdr)

    xDeck = ""  #Add NAME tag NAME:Arcades Aggro
    problematicCards = ""
    for card in deckList["mainboard"]:
        quantity = card["quantity"]
        name = card["name"]
        set = card["set"]
        setNr = card["setNr"]

        if "//" in name:  # Fix adventure cards e.g. Bonecrusher Giant // Stomp => Bonecrusher Giant
            problematicCards += name + "| "
            name = name[:name.index("//")-1]

        line = f"{quantity} [{set}:{setNr}] {name}\n"
        xDeck += line
    
    for card in deckList["sideboard"]:
        quantity = card["quantity"]
        name = card["name"]
        set = card["set"]
        setNr = card["setNr"]

        if "//" in name:
            problematicCards += "[SB]" + name + "| "
            name = name[:name.index("//")-1]

        line = f"SB: {quantity} [{set}:{setNr}] {name}\n"
        xDeck += line

    if problematicCards != "":
        print("     [!]", problematicCards.count('|'), "card(s) might not have been imported. Run in verbose mode (-v) for more info")
    return xDeck

def writeXmageToPath(xmageFolderPath, deckName, format, deckContent):
    #print(xmageFolderPath + "\\" + deckName + ".dck")                    #Logging
    xmageFolderPath = os.path.join(xmageFolderPath, format)
    if not (os.path.exists(xmageFolderPath)):
        os.makedirs(xmageFolderPath)

    # Remove bad characters
    deckName = "".join(i for i in deckName if i not in "/:*?<>|")
    f = open(os.path.join(xmageFolderPath, deckName) + ".dck", "w", encoding='utf-8')
    f.write(deckContent)
    f.close()

def extract_deck_id(moxfield_link):
    # Extract the deck ID from a Moxfield link
    match = re.search(r'/decks/([a-zA-Z0-9_-]+)', moxfield_link)
    return match.group(1) if match else None

class MoxField:
    username = ""
    xmageFolderPath = ""

    def __init__(self, username, xmageFolderPath):
        self.username = username
        self.xmageFolderPath = xmageFolderPath #+ "\\Moxfield"

    def __getUserDecks(self):
        url = (
            "https://api.moxfield.com/v2/users/" +
            self.username + "/decks?pageNumber=1&pageSize=99999"
        )
        # Logging
        print(f"Grabbing <{self.username}>'s public decks from " + url)
        # proxies = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}
        # response = requests.get('http://httpbin.org/headers')
        # https://www.th3r3p0.com/random/python-requests-and-burp-suite.html
        
        r = requests.get(url, headers={'User-Agent': user_agent_list[random.randint(0, len(user_agent_list)-1)]})
        j = json.loads(r.text)
        # printJson(j)
        return j

    def __getDecklist(self, deckId):
        # https://api.moxfield.com/v2/decks/all/g5uBDBFSe0OzEoC_jRInQw
        url = "https://api.moxfield.com/v2/decks/all/" + deckId
        # print(f"Grabbing decklist <{deckId}>")                        #Logging
        r = requests.get(url, headers={'User-Agent': user_agent_list[random.randint(0, len(user_agent_list)-1)]})
        jsonGet = json.loads(r.text)

        deckList = deepcopy(DeckListTemplate)
        deckList["format"] = jsonGet["format"]

        if jsonGet["commandersCount"] != 0:
            for cmdr in jsonGet["commanders"]:
                cardFormat = deepcopy(CardFormatTemplate)
                specificCard = jsonGet["commanders"][cmdr]

                cardFormat["name"] = cmdr
                cardFormat["quantity"] = specificCard["quantity"]
                cardFormat["set"] = specificCard["card"]["set"].upper()
                cardFormat["setNr"] = specificCard["card"]["cn"]
                deckList["commanders"].append(cardFormat)

        if jsonGet["companionsCount"] != 0:
            print(url)
            for comp in jsonGet["companions"]:
                cardFormat = deepcopy(CardFormatTemplate)
                specificCard = jsonGet["companions"][comp]
                
                cardFormat["name"] = comp
                cardFormat["quantity"] = specificCard["quantity"]
                cardFormat["set"] = specificCard["card"]["set"].upper()
                cardFormat["setNr"] = specificCard["card"]["cn"]
                deckList["companions"].append(cardFormat)

        for card in jsonGet["mainboard"]:
            cardFormat = deepcopy(CardFormatTemplate)
            specificCard = jsonGet["mainboard"][card]

            cardFormat["name"] = card
            cardFormat["quantity"] = specificCard["quantity"]
            cardFormat["set"] = specificCard["card"]["set"].upper()
            cardFormat["setNr"] = specificCard["card"]["cn"]
            deckList["mainboard"].append(cardFormat)

        for card in jsonGet["sideboard"]:
            cardFormat = deepcopy(CardFormatTemplate)
            specificCard = jsonGet["sideboard"][card]

            cardFormat["name"] = card
            cardFormat["quantity"] = specificCard["quantity"]
            cardFormat["set"] = specificCard["card"]["set"].upper()
            cardFormat["setNr"] = specificCard["card"]["cn"]
            deckList["sideboard"].append(cardFormat)

        return deckList

    def Download(self):
        # printBanner("moxfield")
        print("Only public decks are searchable in Moxfield")
        userDecks = self.__getUserDecks()
        i, total = 1, len(userDecks["data"])
        for deckName in userDecks["data"]:
            print(f"({i}/{total}) " + deckName["name"] + " " * (50 -
                  len(deckName["name"]) - len(str(i))) + deckName["publicUrl"])
            i = i + 1
            deckJson = self.__getDecklist(deckName["publicId"])
            xDeck = convertDeckToXmage(deckJson)
            writeXmageToPath(self.xmageFolderPath,
                             deckName["name"], deckName["format"], xDeck)
            
    def convertLinkToXmage(self, moxfield_link):
        # Extract deck ID from the provided link
        deck_id = extract_deck_id(moxfield_link)
        if not deck_id:
            print("Invalid Moxfield link.")
            return

        print(f"Converting deck from link: {moxfield_link}")
        deck_list = self.__getDecklist(deck_id)
        xDeck = convertDeckToXmage(deck_list)
        writeXmageToPath(self.xmageFolderPath, deck_list["commanders"][0]["name"], deck_list["format"], xDeck)


# Needs to be changed with -v/-vv/-vvv
# Critical, Error, Warning, Info, Debug
logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.ERROR)


def createArgs():  # Customise the argument handler
    parser = argparse.ArgumentParser(
        description='MTG-To-Xmage | Download your online MTG decks to the XMage format')
    # Moxfield username
    parser.add_argument('-moxfield', metavar="username",
                        help='Your username for Moxfield')
    
    # Moxfield deck link
    parser.add_argument('-link', metavar="moxfield_link",
                        help='Link to the Moxfield deck')

    # Path to folder
    parser.add_argument('-o', metavar="path",
                        help='Path to the folder to download your decks to')

    # Verbose mode
    parser.add_argument('-v', action='store_true', help='Verbose mode')
    # Super Verbose mode
    parser.add_argument('-vv', action='store_true', help='Super Verbose mode')

    # If no arguments were submitted, print help
    #args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
    args = parser.parse_args()
    return args

def main():
    args = createArgs()
    if args.v:
        print("Verbose mode")
    elif args.vv:
        print("Super verbose mode")
    """
    logging.debug("Debug")
    logging.info("Info")
    logging.warning("Warning")
    logging.error("Error")
    logging.critical("Critical")
    """

    config = {"folder": "", "moxfield": ""}
    if os.path.exists("./config.json"):  # If there exists a
        tmp = open("./config.json", "r").read()
        config = json.loads(tmp)

    if args.o is not None:              # If -o [path] is set, update the value
        config["folder"] = args.o
    else:
        if config["folder"] == "":
            config["folder"] = r"./decks"

    if args.moxfield is not None:
        print("Moxfield set")
        config["moxfield"] = args.moxfield

    with open("config.json", "w") as f:
        f.write(json.dumps(config, indent=4))
        f.close()

    urlLink = args.link
    # printJson(config)
    if args.link:
        MoxField(config["moxfield"], config["folder"]).convertLinkToXmage(urlLink)
    elif config["moxfield"] != "":  # Is config has a username for moxfield, start downloading
        print("Starting Moxfield | " + config["moxfield"])
        MoxField(config["moxfield"], config["folder"]).Download()

if __name__ == "__main__":
    main()
