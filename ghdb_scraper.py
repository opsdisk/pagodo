#!/usr/bin/env python

# Standard Python libraries.
import argparse
import json

# Third party Python libraries.
from bs4 import BeautifulSoup
import requests

# Custom Python libraries.


__version__ = "1.0.0"

"""
Dork dictionary example:

{
    "id": "2",
    "date": "2003-06-24",
    "url_title": "<a href='/ghdb/2'>intitle: 'Ganglia 'Cluster Report for'</a>",
    "cat_id": [
        "8",
        "Files Containing Juicy Info"
    ],
    "author_id": [
        "2168",
        "anonymous"
    ],
    "author": {
        "id": "2168",
        "name": "anonymous"
    },
    "category": {
        "cat_id": "8",
        "cat_title": "Files Containing Juicy Info",
        "cat_description": "No usernames or passwords, but interesting stuff none the less.",
        "last_update": "2020-06-12",
        "records_count": "845",
        "porder": 0
    }
}
"""


def retrieve_google_dorks(
    save_json_response_to_file=False, save_all_dorks_to_file=False, save_individual_categories_to_files=False
):
    """Retrieves all google dorks from https://www.exploit-db.com/google-hacking-database and optionally, writes the
    entire json response to a .json file, all the dorks to a file, and/or the individual dork categories to a file.  A
    dictionary is returned containing the total_dorks, a list of extracteddorks, and a category dictionary.
    """

    url = "https://www.exploit-db.com/google-hacking-database"

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "deflate, gzip, br",
        "Accept-Language": "en-US",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0",
        "X-Requested-With": "XMLHttpRequest",
    }

    print(f"[+] Requesting URL: {url}")
    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code != 200:
        print(f"[-] Error retrieving google dorks from: {url}")
        return

    # Extract json data.
    json_response = response.json()

    # Extract recordsTotal and data.
    total_dorks = json_response["recordsTotal"]
    json_dorks = json_response["data"]

    # List to track all the dorks.
    extracted_dorks = []

    # Dictionary to organize the dorks by category.
    category_dict = {}

    # Loop through dorks, collecting and organizing them.
    for dork in json_dorks:

        # Extract dork from <a href> using BeautifulSoup.
        # "<a href=\"/ghdb/5052\">inurl:_cpanel/forgotpwd</a>"
        soup = BeautifulSoup(dork["url_title"], "html.parser")
        # Some of the URL titles have trailing tabs, remove them.
        extracted_dork = soup.find("a").contents[0].strip()
        extracted_dorks.append(extracted_dork)

        # For individual categories.
        # Cast numeric_category_id as integer for sorting later.
        numeric_category_id = int(dork["category"]["cat_id"])
        category_name = dork["category"]["cat_title"]

        # Create an empty list for each category if it doesn't already exist.
        if numeric_category_id not in category_dict:

            category_dict[numeric_category_id] = {"category_name": category_name, "dorks": []}

        # Some of the URL titles have trailing tabs, use replace() to remove it in place.  The strip() method cannot be
        # used because the tab is not at the end of the string, but between the <a> tags instead:
        # <a href="/ghdb/2696">"Powered by Rock Band CMS 0.10"    </a>
        dork["url_title"] = dork["url_title"].replace("\t", "")
        category_dict[numeric_category_id]["dorks"].append(dork)

    # If requested, break up dorks into individual files based off category.
    if save_individual_categories_to_files:

        # Sort category_dict based off the numeric keys.
        category_dict = dict(sorted(category_dict.items()))

        for key, value in category_dict.items():

            # Provide some category metrics.
            print(f"[*] Category {key} ('{value['category_name']}') has {len(value['dorks'])} dorks")

            dork_file_name = value["category_name"].lower().replace(" ", "_")
            full_dork_file_name = f"dorks/{dork_file_name}.dorks"

            print(f"[*] Writing dork category '{value['category_name']}' to file: {full_dork_file_name}")

            with open(f"{full_dork_file_name}", "w", encoding="utf-8") as fh:
                for dork in value["dorks"]:
                    # Extract dork from <a href> using BeautifulSoup.
                    # "<a href=\"/ghdb/5052\">inurl:_cpanel/forgotpwd</a>"
                    soup = BeautifulSoup(dork["url_title"], "html.parser")
                    # Some of the URL titles have trailing tabs, remove them.
                    extracted_dork = soup.find("a").contents[0].strip()
                    fh.write(f"{extracted_dork}\n")

    # Save GHDB json object to all_google_dorks.json.
    if save_json_response_to_file:
        google_dork_json_file = "all_google_dorks.json"
        print(f"[*] Writing all dorks to JSON file: {google_dork_json_file}")
        with open(f"dorks/{google_dork_json_file}", "w", encoding="utf-8") as json_file:
            json.dump(json_dorks, json_file)

    # Save all dorks to all_google_dorks.txt.
    if save_all_dorks_to_file:
        google_dork_file = "all_google_dorks.txt"
        print(f"[*] Writing all dorks to txt file: dorks/{google_dork_file}")
        with open(f"dorks/{google_dork_file}", "w", encoding="utf-8") as fh:
            for dork in extracted_dorks:
                fh.write(f"{dork}\n")

    print(f"[*] Total Google dorks retrieved: {total_dorks}")

    # Package up a nice dictionary to return.
    # fmt: off
    ghdb_dict = {
        "total_dorks": total_dorks,
        "extracted_dorks": extracted_dorks,
        "category_dict": category_dict,
    }
    # fmt: on

    return ghdb_dict


if __name__ == "__main__":

    categories = {
        1: "Footholds",
        2: "File Containing Usernames",
        3: "Sensitives Directories",
        4: "Web Server Detection",
        5: "Vulnerable Files",
        6: "Vulnerable Servers",
        7: "Error Messages",
        8: "File Containing Juicy Info",
        9: "File Containing Passwords",
        10: "Sensitive Online Shopping Info",
        11: "Network or Vulnerability Data",
        12: "Pages Containing Login Portals",
        13: "Various Online devices",
        14: "Advisories and Vulnerabilities",
    }

    epilog = f"Dork categories:\n\n{json.dumps(categories, indent=4)}"

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            f"GHDB Scraper v{__version__} - Retrieve Google Hacking Database dorks from "
            "https://www.exploit-db.com/google-hacking-database."
        ),
        epilog=epilog,
    )

    parser.add_argument(
        "-i",
        dest="save_individual_categories_to_files",
        action="store_true",
        default=False,
        help="Write all the individual dork categories types to separate files.",
    )

    parser.add_argument(
        "-j",
        dest="save_json_response_to_file",
        action="store_true",
        default=False,
        help="Save GHDB json response to all_google_dorks.json",
    )

    parser.add_argument(
        "-s",
        dest="save_all_dorks_to_file",
        action="store_true",
        default=False,
        help="Save all the Google dorks to all_google_dorks.txt",
    )

    args = parser.parse_args()

    retrieve_google_dorks(**vars(args))
