#!/usr/bin/env python

# Standard Python libraries.
import argparse
import json
import time

# Third party Python libraries.
import requests
from bs4 import BeautifulSoup  # noqa

# Custom Python libraries.


def retrieve_google_dorks(save_json_response_to_file, save_dorks):
    """Retrieves all google dorks from https://www.exploit-db.com/google-hacking-database
    Writes then entire json reponse to a file in addition to just the dorks.
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

    if save_json_response_to_file:
        with open("google_dorks.json", "w") as json_file:
            json.dump(json_dorks, json_file)

    if save_dorks:
        google_dork_file = f"google_dorks_{get_timestamp()}.txt"
        with open(google_dork_file, "w") as fh:
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

    parser = argparse.ArgumentParser(
        description="GHDB Scraper - Retrieve the Google Hacking Database dorks from https://www.exploit-db.com/google-hacking-database"
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
        dest="save_dorks",
        action="store_true",
        default=False,
        help="Save the Google dorks to google_dorks_<TIMESTAMP>.txt file",
    )

    args = parser.parse_args()

    print(f"[*] Initiation timestamp: {get_timestamp()}")

    retrieve_google_dorks(**vars(args))

    print(f"[*] Completion timestamp: {get_timestamp()}")

    print("[+] Done!")
