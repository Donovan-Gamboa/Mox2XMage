
# MTG-To-Xmage README

## Overview
MTG-To-Xmage is a Python tool that allows users to download Magic: The Gathering (MTG) decks from Moxfield and convert them into the XMage format for easy import into XMage. With this tool, you can download all public decks for a given Moxfield username or convert a specific deck using a direct link. The downloaded decks are saved in `.dck` format, ready for XMage import.

## Features
- **Fetch all public decks** from a specified Moxfield username.
- **Convert individual Moxfield deck links** into the XMage-compatible `.dck` format.
- **Organize decks by format** and automatically handle XMage-compatible folder structure.
- **Verbose logging** to monitor the conversion process.
- **User-agent randomization** to prevent access blocking.

## Requirements
- **Python 3.6+**
- **BeautifulSoup4**: For HTML parsing
- **Requests**: For handling HTTP requests to the Moxfield API

Install the dependencies using:
```bash
pip install -r requirements.txt
```

## Usage

### Command-line Arguments
- **`-moxfield`**: Fetch and convert all public decks from a Moxfield username.
  ```bash
  python mtg_to_xmage.py -moxfield <username> -o <output_folder>
  ```
- **`-link`**: Convert a specific deck from a Moxfield link.
  ```bash
  python mtg_to_xmage.py -link <moxfield_deck_link> -o <output_folder>
  ```
- **`-o`**: Specifies the output folder where the `.dck` files will be saved.
- **`-v`**: Enable verbose mode for detailed logging.
- **`-vv`**: Enable super verbose mode for extra logging.

### Examples
1. Download all decks from a Moxfield username:
   ```bash
   python mtg_to_xmage.py -moxfield user123 -o decks/
   ```
2. Convert a specific Moxfield deck link to XMage format:
   ```bash
   python mtg_to_xmage.py -link https://www.moxfield.com/decks/abc123 -o decks/
   ```

## Code Overview

- **`MoxField` Class**: Handles interactions with the Moxfield API, retrieving deck lists and individual deck details.
  - **`Download()`**: Fetches and converts all public decks of a specified Moxfield user.
  - **`convertLinkToXmage()`**: Converts a single Moxfield deck from a provided link to XMage format.
- **`convertDeckToXmage()` Function**: Converts a Moxfield deck structure to XMage-compatible `.dck` format.
- **`writeXmageToPath()` Function**: Writes the converted XMage deck to the specified folder.
- **`createArgs()` Function**: Sets up command-line argument parsing.
- **`main()` Function**: Entry point to execute based on command-line arguments.

## Logging
The script uses `logging` for customizable log levels. Run with `-v` or `-vv` for increased output detail.
>Still under consturction at the moment.

## Notes
- **Public Decks Only**: Only public Moxfield decks are accessible via this script.
- **Deck Formatting**: Adventure cards (e.g., `Bonecrusher Giant // Stomp`) and other multi-part cards are partially handled. For best results, inspect converted decks manually.

## License
This project is licensed under the MIT License.
