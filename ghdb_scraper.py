#!/usr/bin/env python

# Standard Python libraries.
import argparse
import json
import time

# Third party Python libraries.
import requests
from bs4 import BeautifulSoup  # noqa

# Custom Python libraries.


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


def retrieve_google_dorks(save_json_response_to_file, save_all_dorks, save_individual_categories):
    """Retrieves all google dorks from https://www.exploit-db.com/google-hacking-database and writes then entire json
    reponse to a file, all the dorks, and/or the individual dork categories.
    """

    url = "https://www.exploit-db.com/google-hacking-database"

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "deflate, gzip, br",
        "Accept-Language": "en-US",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0",
        "X-Requested-With": "XMLHttpRequest",
    }

    response = requests.get(url, headers=headers, verify=True)

    if response.status_code != 200:
        print(f"[-] Error retrieving google dorks from: {url}")
        return

    # Extract json data.
    json_response = response.json()

    # Extract recordsTotal and data.
    total_records = json_response["recordsTotal"]
    json_dorks = json_response["data"]

    # Break up dorks into individual files based off category.
    if save_individual_categories:

        # Initialize a new dictionary to organize the dorks by category.
        category_dict = {}

        for dork in json_dorks:

            # Cast numeric_category_id as integer for sorting later.
            numeric_category_id = int(dork["category"]["cat_id"])
            category_name = dork["category"]["cat_title"]

            # Create an empty list for each category if it doesn't already exist.
            if numeric_category_id not in category_dict:
                # fmt: off
                category_dict[numeric_category_id] = {
                    "category_name": category_name,
                    "dorks": [],
                }
                # fmt: on

            category_dict[numeric_category_id]["dorks"].append(dork)

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
                    extracted_dork = soup.find("a").contents[0]
                    fh.write(f"{extracted_dork}\n")

    # Save .json file containing dorks.
    if save_json_response_to_file:
        print("[*] Writing all dorks to JSON file: dorks/google_dorks.json")
        with open("dorks/google_dorks.json", "w", encoding="utf-8") as json_file:
            json.dump(json_dorks, json_file)

    # Save all dorks to a file.
    if save_all_dorks:
        google_dork_file = f"all_google_dorks_{get_timestamp()}.txt"
        print(f"[*] Writing all dorks to txt file: {google_dork_file}")
        with open(f"dorks/{google_dork_file}", "w", encoding="utf-8") as fh:
            for dork in json_dorks:
                # Extract dork from <a href> using BeautifulSoup.
                # "<a href=\"/ghdb/5052\">inurl:_cpanel/forgotpwd</a>"
                soup = BeautifulSoup(dork["url_title"], "html.parser")
                extracted_dork = soup.find("a").contents[0]
                fh.write(f"{extracted_dork}\n")

    print(f"[*] Total Google dorks retrieved: {total_records}")


def get_timestamp():
    """Retrieve a pre-formated datetimestamp."""

    now = time.localtime()
    timestamp = time.strftime("%Y%m%d_%H%M%S", now)

    return timestamp


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
            "GHDB Scraper - Retrieve the Google Hacking Database dorks from "
            "https://www.exploit-db.com/google-hacking-database."
        ),
        epilog=epilog,
    )

    parser.add_argument(
        "-i",
        dest="save_individual_categories",
        action="store_true",
        default=False,
        help="Write all the individual dork type files based off the category.",
    )

    parser.add_argument(
        "-j",
        dest="save_json_response_to_file",
        action="store_true",
        default=False,
        help="Save json response to a .json file",
    )

    parser.add_argument(
        "-s",
        dest="save_all_dorks",
        action="store_true",
        default=False,
        help="Save the Google dorks to google_dorks_<TIMESTAMP>.txt file",
    )

    args = parser.parse_args()

    print(f"[*] Initiation timestamp: {get_timestamp()}")

    retrieve_google_dorks(**vars(args))

    print(f"[*] Completion timestamp: {get_timestamp()}")

    print("[+] Done!")
