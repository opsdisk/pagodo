#!/usr/bin/env python

# Standard Python libraries.
import argparse
import datetime
import json
import os
import random
import re
import sys
import time

# Third party Python libraries.
import colorama

# Custom Python libraries.
import yagooglesearch

__version__ = "2.0.0"

colorama.init(autoreset=True)


class Pagodo:
    """Pagodo class object"""

    def __init__(
        self,
        google_dorks_file,
        domain="",
        max_search_result_urls_to_return_per_dork=100,
        save_pagodo_results_to_json_file=False,
        proxies="",
        save_urls_to_file=False,
        minimum_delay_between_dork_searches_in_seconds=37,
        maximum_delay_between_dork_searches_in_seconds=60,
        verbosity=4,
    ):
        """Initialize Pagodo class object."""

        self.google_dorks_file = google_dorks_file
        self.google_dorks = []
        with open(google_dorks_file, "r") as fh:
            for line in fh.read().splitlines():
                if line.strip():
                    self.google_dorks.append(line)
        self.domain = domain
        self.max_search_result_urls_to_return_per_dork = max_search_result_urls_to_return_per_dork
        self.save_pagodo_results_to_json_file = save_pagodo_results_to_json_file
        self.proxies = proxies.split(",")
        self.save_urls_to_file = save_urls_to_file
        self.minimum_delay_between_dork_searches_in_seconds = minimum_delay_between_dork_searches_in_seconds
        self.maximum_delay_between_dork_searches_in_seconds = maximum_delay_between_dork_searches_in_seconds
        self.verbosity = verbosity

        # Fancy way of generating a list of 20 random values between minimum_delay_between_dork_searches_in_seconds and
        # maximum_delay_between_dork_searches_in_seconds.  A random value is selected between each different Google
        # dork search.
        """
        1) Generate a random list of values between minimum_delay_between_dork_searches_in_seconds and
           maximum_delay_between_dork_searches_in_seconds
        2) Round those values to the tenths place
        3) Re-case as a list
        4) Sort the list
        """
        self.delay_between_dork_searches_list = sorted(
            list(
                map(
                    lambda x: round(x, 1),
                    [
                        random.uniform(
                            minimum_delay_between_dork_searches_in_seconds,
                            maximum_delay_between_dork_searches_in_seconds,
                        )
                        for _ in range(20)
                    ],
                )
            )
        )

        self.base_file_name = f'pagodo_results_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'
        self.total_urls_found = 0
        self.proxy_rotation_index = 0

    def go(self):
        """Start pagodo Google dork search."""

        initiation_timestamp = datetime.datetime.now().isoformat()

        print(f"[*] Initiation timestamp: {initiation_timestamp}")

        # Initialize starting dork number.
        dork_counter = 1

        total_dorks_to_search = len(self.google_dorks)

        # Initialize dictionary to track dork results.
        self.pagodo_results_dict = {
            "dorks": {},
            "initiation_timestamp": initiation_timestamp,
            "completion_timestamp": "",
        }

        for dork in self.google_dorks:

            # fmt: off
            self.pagodo_results_dict["dorks"][dork] = {
                "urls_size": 0,
                "urls": [],

            }
            # fmt: on

            try:
                dork = dork.strip()

                # Search for the URLs to collect.
                if self.domain:
                    query = f"site:{self.domain} {dork}"
                else:
                    query = dork

                """
                Google search web GUI message for large search string queries:
                    "the" (and any subsequent words) was ignored because we limit queries to 32 words.
                """
                # Search string is longer than 32 words.
                if len(query.split(" ")) > 32:
                    ignored_string = " ".join(query.split(" ")[32:])
                    print(
                        colorama.Fore.YELLOW
                        + "[!] Google limits queries to 32 words (separated by spaces):  Removing from search query: "
                        f"'{ignored_string}'"
                    )

                    # Update query variable.
                    updated_query = " ".join(query.split(" ")[0:32])

                    # If original query is in quotes, append a double quote to new truncated updated_query.
                    if query.endswith('"'):
                        updated_query = f'{updated_query}"'

                    print(f"[*] New search query: {updated_query}")

                    query = updated_query

                # Rotate through the list of proxies using modulus to ensure the index is in the self.proxies list.
                proxy_index = self.proxy_rotation_index % len(self.proxies)
                proxy = self.proxies[proxy_index]
                self.proxy_rotation_index += 1

                # Instantiate a new yagooglesearch.SearchClient object for each Google dork.
                client = yagooglesearch.SearchClient(
                    query,
                    tbs="li:1",  # Verbatim search.
                    num=100,  # Retrieve up to 100 Google search results at time.
                    # Max desired valid URLs per dork.
                    max_search_result_urls_to_return=self.max_search_result_urls_to_return_per_dork,
                    proxy=proxy,
                    verbosity=self.verbosity,
                )

                # Randomize the user agent for best results.
                client.assign_random_user_agent()

                print(
                    f"[*] Search ( {dork_counter} / {total_dorks_to_search} ) for Google dork [ {query} ] using "
                    f"User-Agent '{client.user_agent}' through proxy '{proxy}'"
                )

                dork_urls_list = client.search()

                # Remove any exploit-db.com URLs.
                for url in dork_urls_list:
                    # Ignore results from specific URLs like exploit-db.com, cert.org, and GHDB's twitter account
                    # that may just be providing information about the vulnerability.  Keeping it simple with regex.
                    ignore_url_list = [
                        "https://www.kb.cert.org",
                        "https://www.exploit-db.com/",
                        "https://twitter.com/googlehacking/",
                    ]
                    for ignore_url in ignore_url_list:
                        if re.search(ignore_url, url, re.IGNORECASE):
                            print(colorama.Fore.YELLOW + f"[*] Removing {ignore_url} URL: {url}")
                            dork_urls_list.remove(url)

                dork_urls_list_size = len(dork_urls_list)

                # Google dork results found.
                if dork_urls_list:

                    print(
                        colorama.Fore.GREEN + f"[*] Results: {dork_urls_list_size} URLs found for Google dork: {dork}"
                    )

                    for url in dork_urls_list:
                        print(url)

                    self.total_urls_found += dork_urls_list_size

                    # Save URLs with valid results to an .txt file.
                    if self.save_urls_to_file:
                        with open(f"{self.base_file_name}.txt", "a") as fh:
                            fh.write(f"# {dork}\n")
                            for url in dork_urls_list:
                                fh.write(f"{url}\n")
                            fh.write("#" * 50 + "\n")

                    # fmt: off
                    self.pagodo_results_dict["dorks"][dork] = {
                        "urls_size": dork_urls_list_size,
                        "urls": dork_urls_list,
                    }
                    # fmt: on

                # No Google dork results found.
                else:
                    print(f"[*] Results: {dork_urls_list_size} URLs found for Google dork: {dork}")

            except KeyboardInterrupt:
                sys.exit(0)

            except Exception as e:
                print(colorama.Fore.YELLOW + f"[-] Error with dork: {dork}")
                print(colorama.Fore.YELLOW + f"[-] EXCEPTION: {e}")

            dork_counter += 1

            # Only sleep if there are more dorks to search.
            if dork != self.google_dorks[-1]:
                pause_time = random.choice(self.delay_between_dork_searches_list)
                print(f"[*] Sleeping {pause_time} seconds before executing the next dork search...")
                time.sleep(pause_time)

        print(f"[*] Total URLs found for the {total_dorks_to_search} total dorks searched: {self.total_urls_found}")

        completion_timestamp = datetime.datetime.now().isoformat()

        print(f"[*] Completion timestamp: {completion_timestamp}")
        self.pagodo_results_dict["completion_timestamp"] = completion_timestamp

        # Save pagodo_results_dict to a .json file.
        if self.save_pagodo_results_to_json_file:
            with open(f"{self.base_file_name}.json", "w") as fh:
                json.dump(self.pagodo_results_dict, fh, indent=4)

        return self.pagodo_results_dict


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=f"pagodo - Passive Google Dork v{__version__}")
    parser.add_argument(
        "-g", dest="google_dorks_file", action="store", required=True, help="File containing Google dorks, 1 per line."
    )
    parser.add_argument(
        "-d",
        dest="domain",
        action="store",
        required=False,
        help="Domain to scope the Google dork searches.  Not required.",
    )
    parser.add_argument(
        "-i",
        dest="minimum_delay_between_dork_searches_in_seconds",
        action="store",
        required=False,
        type=int,
        default=37,
        help=("Minimum delay (in seconds) between a Google dork search.  Default: 37"),
    )
    parser.add_argument(
        "-x",
        dest="maximum_delay_between_dork_searches_in_seconds",
        action="store",
        required=False,
        type=int,
        default=60,
        help=("Maximum delay (in seconds) between a Google dork search.  Default: 60"),
    )
    parser.add_argument(
        "-m",
        dest="max_search_result_urls_to_return_per_dork",
        action="store",
        required=False,
        type=int,
        default=100,
        help="Maximum results to search per dork.  Default 100.",
    )
    parser.add_argument(
        "-p",
        dest="proxies",
        action="store",
        required=False,
        type=str,
        default="",
        help=(
            "Comma separated string of proxies to round-robin through.  Example: "
            "https://myproxy:8080,socks5h://127.0.0.1:9050,socks5h://127.0.0.1:9051.  The proxy scheme must confrom "
            "per the Python requests library: https://docs.python-requests.org/en/master/user/advanced/#proxies  See "
            "https://github.com/opsdisk/yagooglesearch for more information."
        ),
    )
    parser.add_argument(
        "-o",
        dest="save_pagodo_results_to_json_file",
        action="store_true",
        required=False,
        default=False,
        help=(
            "Save JSON dictionary to pagodo_results_<TIMESTAMP>.json file.  Contains more information than "
            "pagodo_results_<TIMESTAMP>.txt"
        ),
    )
    parser.add_argument(
        "-s",
        dest="save_urls_to_file",
        action="store_true",
        required=False,
        default=False,
        help="Save any URLS found for a dork to the pagodo_results_<TIMESTAMP>.txt file.",
    )
    parser.add_argument(
        "-v",
        dest="verbosity",
        action="store",
        type=int,
        default=4,
        help="Verbosity level (0=NOTSET, 1=CRITICAL, 2=ERROR, 3=WARNING, 4=INFO, 5=DEBUG).  Default: 4",
    )

    args = parser.parse_args()

    if not os.path.exists(args.google_dorks_file):
        print(colorama.Fore.YELLOW + "[!] Specify a valid file containing Google dorks with -g")
        sys.exit(0)

    if args.minimum_delay_between_dork_searches_in_seconds < 0:
        print(colorama.Fore.YELLOW + "[!] Minimum delay between dork searches must be greater than 0")
        sys.exit(0)

    if args.maximum_delay_between_dork_searches_in_seconds < 0:
        print(colorama.Fore.YELLOW + "[!] maximum_delay_between_dork_searches_in_seconds must be greater than 0")
        sys.exit(0)

    if args.maximum_delay_between_dork_searches_in_seconds <= args.minimum_delay_between_dork_searches_in_seconds:
        print(
            colorama.Fore.YELLOW + "[!] maximum_delay_between_dork_searches_in_seconds must be greater than "
            "minimum_delay_between_dork_searches_in_seconds"
        )
        sys.exit(0)

    if args.max_search_result_urls_to_return_per_dork < 0:
        print(colorama.Fore.YELLOW + "[!] max_search_result_urls_to_return_per_dork must be greater than 0")
        sys.exit(0)

    pagodo = Pagodo(**vars(args))
    pagodo.go()
