#!/usr/bin/env python

# Standard Python libraries.
import argparse
import datetime
import json
import logging
import os
import random
import re
import sys
import time

# Third party Python libraries.
import yagooglesearch

# Custom Python libraries.


__version__ = "2.6.0"


class Pagodo:
    """Pagodo class object"""

    def __init__(
        self,
        google_dorks_file,
        domain="",
        max_search_result_urls_to_return_per_dork=100,
        save_pagodo_results_to_json_file=None,  # None = Auto-generate file name, otherwise pass a string for path and filename.
        proxies="",
        save_urls_to_file=None,  # None = Auto-generate file name, otherwise pass a string for path and filename.
        minimum_delay_between_dork_searches_in_seconds=37,
        maximum_delay_between_dork_searches_in_seconds=60,
        disable_verify_ssl=False,
        verbosity=4,
        specific_log_file_name="pagodo.py.log",
    ):
        """Initialize Pagodo class object."""

        # Logging
        self.log = logging.getLogger("pagodo")
        log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)s] %(message)s")

        # Setup file logging.
        log_file_handler = logging.FileHandler(specific_log_file_name)
        log_file_handler.setFormatter(log_formatter)
        self.log.addHandler(log_file_handler)

        # Setup console logging.
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        self.log.addHandler(console_handler)

        # Assign log level.
        self.verbosity = verbosity
        self.log.setLevel((6 - self.verbosity) * 10)

        # Run parameter checks.
        if not os.path.exists(google_dorks_file):
            print("Specify a valid file containing Google dorks with -g")
            sys.exit(0)

        if minimum_delay_between_dork_searches_in_seconds < 0:
            print("Minimum delay between dork searches (-i) must be greater than 0")
            sys.exit(0)

        if maximum_delay_between_dork_searches_in_seconds < 0:
            print("maximum_delay_between_dork_searches_in_seconds (-x) must be greater than 0")
            sys.exit(0)

        if maximum_delay_between_dork_searches_in_seconds <= minimum_delay_between_dork_searches_in_seconds:
            print(
                "maximum_delay_between_dork_searches_in_seconds (-x) must be greater than "
                "minimum_delay_between_dork_searches_in_seconds (-i)"
            )
            sys.exit(0)

        if max_search_result_urls_to_return_per_dork < 0:
            print("max_search_result_urls_to_return_per_dork (-m) must be greater than 0")
            sys.exit(0)

        # All passed parameters look good, assign to the class object.
        self.google_dorks_file = google_dorks_file
        self.google_dorks = []
        with open(google_dorks_file, "r", encoding="utf-8") as fh:
            for line in fh.read().splitlines():
                if line.strip():
                    self.google_dorks.append(line)
        self.domain = domain
        self.max_search_result_urls_to_return_per_dork = max_search_result_urls_to_return_per_dork
        self.save_pagodo_results_to_json_file = save_pagodo_results_to_json_file
        self.proxies = proxies.strip().strip(",").split(",")
        self.save_urls_to_file = save_urls_to_file
        self.minimum_delay_between_dork_searches_in_seconds = minimum_delay_between_dork_searches_in_seconds
        self.maximum_delay_between_dork_searches_in_seconds = maximum_delay_between_dork_searches_in_seconds
        self.disable_verify_ssl = disable_verify_ssl

        # Fancy way of generating a list of 20 random values between minimum_delay_between_dork_searches_in_seconds and
        # maximum_delay_between_dork_searches_in_seconds.  A random value is selected between each different Google
        # dork search.
        """
        1) Generate a random list of values between minimum_delay_between_dork_searches_in_seconds and
           maximum_delay_between_dork_searches_in_seconds
        2) Round those values to the tenths place
        3) Re-cast as a list
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

        # -o with no filename.  Desire to save results, don't care about the file name.
        if self.save_pagodo_results_to_json_file is None:
            self.save_pagodo_results_to_json_file = f"{self.base_file_name}.json"

        # -s with no filename.  Desire to save results, don't care about the file name.
        if self.save_urls_to_file is None:
            self.save_urls_to_file = f"{self.base_file_name}.txt"

    def go(self):
        """Start pagodo Google dork search."""

        initiation_timestamp = datetime.datetime.now().isoformat()

        self.log.info(f"Initiation timestamp: {initiation_timestamp}")

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
            self.pagodo_results_dict["dorks"][dork] = {
                "urls_size": 0,
                "urls": [],
            }

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
                    self.log.warning(
                        "Google limits queries to 32 words (separated by spaces):  Removing from search query: "
                        f"'{ignored_string}'"
                    )

                    # Update query variable.
                    updated_query = " ".join(query.split(" ")[0:32])

                    # If original query is in quotes, append a double quote to new truncated updated_query.
                    if query.endswith('"'):
                        updated_query = f'{updated_query}"'

                    self.log.info(f"New search query: {updated_query}")

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
                    # Max desired valid URLs to collect per dork.
                    max_search_result_urls_to_return=self.max_search_result_urls_to_return_per_dork,
                    proxy=proxy,
                    verify_ssl=not self.disable_verify_ssl,
                    verbosity=self.verbosity,
                )

                # Randomize the user agent for best results.
                client.assign_random_user_agent()

                self.log.info(
                    f"Search ( {dork_counter} / {total_dorks_to_search} ) for Google dork [ {query} ] using "
                    f"User-Agent '{client.user_agent}' through proxy '{proxy}'"
                )

                dork_urls_list = client.search()

                # Remove any false positive URLs.
                for url in dork_urls_list:
                    # Ignore results from specific URLs like exploit-db.com, cert.org, and OffSec's Twitter account that
                    # may just be providing information about the vulnerability.  Keeping it simple with regex.
                    ignore_url_list = [
                        "https://www.kb.cert.org",
                        "https://www.exploit-db.com/",
                        "https://twitter.com/ExploitDB/",
                    ]
                    for ignore_url in ignore_url_list:
                        if re.search(ignore_url, url, re.IGNORECASE):
                            self.log.warning(f"Removing {ignore_url} false positive URL: {url}")
                            dork_urls_list.remove(url)

                dork_urls_list_size = len(dork_urls_list)

                # Google dork results found.
                if dork_urls_list:
                    self.log.info(f"Results: {dork_urls_list_size} URLs found for Google dork: {dork}")

                    dork_urls_list_as_string = "\n".join(dork_urls_list)
                    self.log.info(f"dork_urls_list:\n{dork_urls_list_as_string}")

                    self.total_urls_found += dork_urls_list_size

                    # Save URLs with valid results to an .txt file.
                    if self.save_urls_to_file:
                        with open(self.save_urls_to_file, "a") as fh:
                            fh.write(f"# {dork}\n")
                            for url in dork_urls_list:
                                fh.write(f"{url}\n")
                            fh.write("#" * 50 + "\n")

                    self.pagodo_results_dict["dorks"][dork] = {
                        "urls_size": dork_urls_list_size,
                        "urls": dork_urls_list,
                    }

                # No Google dork results found.
                else:
                    self.log.info(f"Results: {dork_urls_list_size} URLs found for Google dork: {dork}")

            except KeyboardInterrupt:
                sys.exit(0)

            except Exception as e:
                self.log.error(f"Error with dork: {dork}.  Exception {e}")
                if type(e).__name__ == "SSLError" and (not self.disable_verify_ssl):
                    self.log.info(
                        "If you are using self-signed certificates for an HTTPS proxy, try-rerunning with the -l "
                        "switch to disable verifying SSL/TLS certificates.  Exiting..."
                    )
                    sys.exit(1)

            dork_counter += 1

            # Only sleep if there are more dorks to search.
            if dork != self.google_dorks[-1]:
                pause_time = random.choice(self.delay_between_dork_searches_list)
                self.log.info(f"Sleeping {pause_time} seconds before executing the next dork search...")
                time.sleep(pause_time)

        self.log.info(f"Total URLs found for the {total_dorks_to_search} total dorks searched: {self.total_urls_found}")

        completion_timestamp = datetime.datetime.now().isoformat()

        self.log.info(f"Completion timestamp: {completion_timestamp}")
        self.pagodo_results_dict["completion_timestamp"] = completion_timestamp

        # Save pagodo_results_dict to a .json file.
        if self.save_pagodo_results_to_json_file:
            with open(self.save_pagodo_results_to_json_file, "w") as fh:
                json.dump(self.pagodo_results_dict, fh, indent=4)

        return self.pagodo_results_dict


# http://stackoverflow.com/questions/3853722/python-argparse-how-to-insert-newline-in-the-help-text
class SmartFormatter(argparse.HelpFormatter):
    def _split_lines(self, text, width):
        if text.startswith("R|"):
            return text[2:].splitlines()
        # This is the RawTextHelpFormatter._split_lines
        return argparse.HelpFormatter._split_lines(self, text, width)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=f"pagodo - Passive Google Dork v{__version__}",
        formatter_class=SmartFormatter,
    )
    parser.add_argument(
        "-g",
        dest="google_dorks_file",
        action="store",
        required=True,
        help="File containing Google dorks, 1 per line.",
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
        help="Minimum delay (in seconds) between a Google dork search.  Default: 37",
    )
    parser.add_argument(
        "-x",
        dest="maximum_delay_between_dork_searches_in_seconds",
        action="store",
        required=False,
        type=int,
        default=60,
        help="Maximum delay (in seconds) between a Google dork search.  Default: 60",
    )
    parser.add_argument(
        "-l",
        dest="disable_verify_ssl",
        action="store_true",
        required=False,
        default=False,
        help="Disable SSL/TLS validation.  Sometimes required if using an HTTPS proxy with self-signed certificates.",
    )
    parser.add_argument(
        "-m",
        dest="max_search_result_urls_to_return_per_dork",
        action="store",
        required=False,
        type=int,
        default=100,
        help="Maximum results to return per dork.  Default 100.",
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
            "https://myproxy:8080,socks5h://127.0.0.1:9050,socks5h://127.0.0.1:9051 - The proxy scheme must conform "
            "per the Python requests library: https://docs.python-requests.org/en/master/user/advanced/#proxies  Also "
            "see https://github.com/opsdisk/yagooglesearch for more information."
        ),
    )
    parser.add_argument(
        "-o",
        nargs="?",
        metavar="JSON_FILE",
        dest="save_pagodo_results_to_json_file",
        action="store",
        default=False,
        help="R|Save URL dork data to a JSON file.  Contains more information than .txt version\n"
        "no -o = Do not save dork data to a JSON file\n"
        "-o = Save dork data to pagodo_results_<TIMESTAMP>.json\n"
        "-o JSON_FILE = Save dork data to JSON_FILE",
    )
    parser.add_argument(
        "-s",
        nargs="?",
        metavar="URL_FILE",
        dest="save_urls_to_file",
        action="store",
        default=False,
        help="R|Save URL dork data to a text file.\n"
        "no -s = Do not save dork data to a file\n"
        "-s = Save dork data to pagodo_results_<TIMESTAMP>.txt\n"
        "-s URL_FILE = Save dork data to URL_FILE",
    )
    parser.add_argument(
        "-v",
        dest="verbosity",
        action="store",
        type=int,
        default=4,
        help="Verbosity level (0=NOTSET, 1=CRITICAL, 2=ERROR, 3=WARNING, 4=INFO, 5=DEBUG).  Default: 4",
    )
    parser.add_argument(
        "--log",
        dest="specific_log_file_name",
        action="store",
        default="pagodo.py.log",
        required=False,
        help="Save log data to a specific log filename, otherwise the default is pagodo.py.log",
    )

    args = parser.parse_args()

    pagodo = Pagodo(**vars(args))
    pagodo.go()
