#!/usr/bin/env python

# Standard Python libraries.
import argparse
import os
import queue
import sys
import threading
import time

# Third party Python libraries.
import requests
from bs4 import BeautifulSoup  # noqa

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
            url = f"https://www.exploit-db.com/ghdb/{dork_number}"

            headers = {"User-Agent": "Googlebot/2.1 (+http://www.google.com/bot.html"}

            try:
                # exploit-db.com takes a while to load sometimes.
                response = requests.get(url, headers=headers, verify=True, timeout=60)

                # Looking for HTTP 200 status code.
                if response.status_code == 200:
                    page = response.text

                    # Use beautiful soup to drill down to the actual Google dork in the meta tags
                    """
                    <meta property="og:title" content="bash_history files">
                    <meta property="og:type" content="article" />
                    <meta property="og:url" content="https://www.exploit-db.com/ghdb/9/">
                    <meta property="og:image" content="https://www.exploit-db.com/images/spider-orange.png" />
                    <meta property="og:site_name" content="Exploit Database" />
                    <meta property="article:published_time" content="2003-06-24" />
                    <meta property="article:author" content="anonymous" />
                    <meta property="article:authorUrl" content="https://www.exploit-db.com/?author=2168" />
                    """
                    soup = BeautifulSoup(page, "html.parser")
                    dork = soup.find("meta", property="og:title")["content"]

                    try:
                        print(f"[+] Retrieving dork {dork_number}: {dork}")
                        ghdb.dorks.append(dork)

                    except:
                        print(f"[-] Dork number {dork_number} failed: {dork}")

                else:
                    print(f"Could not access {url}. HTTP status code: {response.status_code}")

            except:
                print(f"[-] Random error with dork number {dork_number}.")

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
            print(f"[*] Spawing thread #{i}")
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
            google_dork_file = f"google_dorks_{get_timestamp()}.txt"
            with open(os.path.join(self.save_directory, google_dork_file), "a") as fh:
                # Use set to remove duplicates.
                for dork in set(self.dorks):
                    fh.write(f"{dork}\n")

        print(f"[*] Total Google dorks retrieved: {len(self.dorks)}")


def get_timestamp():
    """Retrieve a pre-formated datetimestamp."""

    now = time.localtime()
    timestamp = time.strftime("%Y%m%d_%H%M%S", now)
    return timestamp


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="GHDB Scraper - Retrieve the Google Hacking Database dorks from https://www.exploit-db.com"
    )
    parser.add_argument(
        "-n",
        dest="min_dork_number",
        action="store",
        type=int,
        default=1,
        help="Minimum Google dork number to start at (Default: 1).",
    )
    parser.add_argument(
        "-x",
        dest="max_dork_number",
        action="store",
        type=int,
        default=5050,
        help="""Maximum Google dork number, not the total, to retrieve (Default: 5050).  It is currently around 5050 as of 2018-12-05.
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
        default=2,
        help="Number of search threads (Default: 2)",
    )

    args = parser.parse_args()

    if args.save_directory:
        print(f"[*] Dork file will be saved here: {args.save_directory}")
        if not os.path.exists(args.save_directory):
            print(f"[+] Creating folder: {args.save_directory}")
            os.mkdir(args.save_directory)

    if args.min_dork_number < 1:
        print("[!] Search Google dork MIN must be 1 or greater (-n).")
        sys.exit(0)

    if args.max_dork_number < 1:
        print("[!] Search Google dork MAX must be 1 or greater (-x).")
        sys.exit(0)

    if args.max_dork_number < args.min_dork_number:
        print("[!] Search Google dork MAX must be greater than dork MIN.")
        sys.exit(0)

    if args.number_of_threads < 0:
        print("[!] Number of threads (-n) must be greater than 0.")
        sys.exit(0)

    print(f"[*] Initiation timestamp: {get_timestamp()}")

    ghdb = GHDBCollector(**vars(args))
    ghdb.go()

    print(f"[*] Completion timestamp: {get_timestamp()}")

    print("[+] Done!")
