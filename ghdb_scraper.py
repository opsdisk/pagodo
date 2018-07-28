#!/usr/bin/env python
# GPL v 3.0 License
# Opsdisk LLC | opsdisk.com

# Standard Python libraries.
import argparse
import os
import queue
import sys
import threading
import time

# Third party Python libraries.
import requests
from bs4 import BeautifulSoup

# Custom Python libraries.


class Worker(threading.Thread):
    """GHDB Scraper Worker class"""

    def __init__(self):
        """Initialize worker thread"""

        threading.Thread.__init__(self)

    def run(self):
        """Start worker thread"""

        while True:
            # Grab URL off the queue and build the request.
            dork_number = ghdb.queue.get()
            url = "https://www.exploit-db.com/ghdb/{}".format(dork_number)

            headers = {"User-Agent": "Googlebot/2.1 (+http://www.google.com/bot.html"}

            try:
                # exploit-db.com takes a while to load sometimes.
                response = requests.get(url, headers=headers, verify=True, timeout=60)

                # Looking for HTTP 200 status code.
                if response.status_code == 200:
                    page = response.text

                    # Use beautiful soup to drill down to the actual Google dork.
                    soup = BeautifulSoup(page, "html.parser")
                    table = soup.find_all("table")[0]
                    column = table.find_all("td")[2]
                    dork = column.find_all("a")[0].contents[0]

                    # Clean up string by removing '\n' characters and spaces.
                    # https://www.exploit-db.com/ghdb/9/
                    # '\n                intitle:index.of .bash_history            ' --> intitle:index.of .bash_history
                    dork = " ".join(dork.split())

                    try:
                        print("[+] Retrieving dork {}: {}".format(dork_number, dork))
                        ghdb.dorks.append(dork)

                    except:
                        print("[-] Dork number {} failed: {}".format(dork_number, dork))

                else:
                    print("Could not access {}. HTTP status code: {}".format(url, response.status_code))

            except:
                print("[-] Random error with dork number {}.".format(dork_number))

            ghdb.queue.task_done()


class GHDBCollector:
    """GHDB collector class"""

    def __init__(self, min_dork_number, max_dork_number, save_directory, save_dorks, number_of_threads):
        """Initialize GHDBCollector class"""

        self.min_dork_number = min_dork_number
        self.max_dork_number = max_dork_number
        self.save_directory = save_directory
        self.save_dorks = save_dorks
        self.dorks = []

        # Create queue and specify the number of worker threads.
        self.queue = queue.Queue()
        self.number_of_threads = number_of_threads

    def go(self):
        """Start collecting Google dorks."""

        # Kickoff the threadpool.
        for i in range(self.number_of_threads):
            print("[*] Spawing thread #{}".format(i))
            thread = Worker()
            thread.daemon = True
            thread.start()

        # Populate the queue with the Google dork range.
        for dork_number in range(self.min_dork_number, self.max_dork_number + 1):
            self.queue.put(dork_number)
        self.queue.join()

        print("-" * 50)
        for dork in self.dorks:
            print(dork)
        print("-" * 50)

        if self.save_dorks:
            google_dork_file = "google_dorks_{}.txt".format(get_timestamp())
            with open(os.path.join(self.save_directory, google_dork_file), "a") as fh:
                # Use set to remove duplicates.
                for dork in set(self.dorks):
                    fh.write("{}\n".format(dork))

        print("[*] Total Google dorks retrieved: {}".format(len(self.dorks)))


def get_timestamp():
    """Retrieve a pre-formated datetimestamp."""

    now = time.localtime()
    timestamp = time.strftime("%Y%m%d_%H%M%S", now)
    return timestamp


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="GHDB Scraper - Retrieve the Google Hacking Database dorks from exploit-db.com"
    )
    parser.add_argument(
        "-n",
        dest="min_dork_number",
        action="store",
        type=int,
        default=5,
        help="Minimum Google dork number to start at (Default: 5).",
    )
    parser.add_argument(
        "-x",
        dest="max_dork_number",
        action="store",
        type=int,
        default=5000,
        help="""Maximum Google dork number, not the total, to retrieve (Default: 5000).  It is currently around 4900.
          There is no logic in this script to determine when it has reached the end.""",
    )
    parser.add_argument(
        "-d",
        dest="save_directory",
        action="store",
        default=os.getcwd(),
        help='Directory to save downloaded files (Default: cwd, ".")',
    )
    parser.add_argument(
        "-s",
        dest="save_dorks",
        action="store_true",
        default=False,
        help="Save the Google dorks to google_dorks_<TIMESTAMP>.txt file",
    )
    parser.add_argument(
        "-t",
        dest="number_of_threads",
        action="store",
        type=int,
        default=3,
        help="Number of search threads (Default: 2)",
    )

    args = parser.parse_args()

    if args.save_directory:
        print("[*] Dork file will be saved here: {}".format(args.save_directory))
        if not os.path.exists(args.save_directory):
            print("[+] Creating folder: " + args.save_directory)
            os.mkdir(args.save_directory)

    if args.min_dork_number < 5:
        print("[!] Search Google Dork MIN must be 5 or greater (-n)")
        sys.exit(0)

    if args.max_dork_number < 5:
        print("[!] Search Google Dork MAX must be 5 or greater (-x)")
        sys.exit(0)

    if args.number_of_threads < 0:
        print("[!] Number of threads (-n) must be greater than 0")
        sys.exit(0)

    print("[*] Initiation timestamp: {}".format(get_timestamp()))
    ghdb = GHDBCollector(**vars(args))
    ghdb.go()
    print("[*] Completion timestamp: {}".format(get_timestamp()))

    print("[+] Done!")
