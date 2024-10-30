import urllib.request
from bs4 import BeautifulSoup

def fetch_deck(deck_id):
    url = f"https://api.moxfield.com/v2/decks/all/{deck_id}"
    try:
        # Send an HTTP GET request
        with urllib.request.urlopen(url) as response:
            bSoup = response.read()
            soup = BeautifulSoup(bSoup, 'html.parser')  # Specify the parser to avoid warnings
            return soup
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")

def convert2Text(soup):
    mainboard = soup.get("mainboard", {})
    # Formatting the output
    for details in mainboard.items():
        card_info = details["card"]
        print(f"Card Name: {card_info['name']}")


def getDeckID(url):
    deckID = url.split('/')[-1]
    return deckID

def main():
    deck_url = input("Enter the Moxfield deck URL: ")
    deck_ID = getDeckID(deck_url)
    deck = fetch_deck(deck_ID)
    
    if deck:  # Check if deck is successfully fetched
        print(deck.prettify())  # Print the parsed HTML nicely

if __name__ == "__main__":
    main()
