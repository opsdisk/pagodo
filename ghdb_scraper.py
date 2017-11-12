#!/usr/bin/env python
# GPL v 3.0 License
# Opsdisk LLC | opsdisk.com
from __future__ import print_function

import argparse
import os
import sys
import threading
import time

# https://stackoverflow.com/questions/29687837/queue-importerror-in-python-3
is_py2 = sys.version[0] == '2'
if is_py2:
    import Queue as queue
else:
    import queue as queue


import requests  # noqa
from bs4 import BeautifulSoup  # noqa


class Worker(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            # Grab URL off the queue and build the request
            dork_number = ghdb.queue.get()
            url = 'https://www.exploit-db.com/ghdb/{0}'.format(dork_number)

            headers = {
                'User-Agent': 'Googlebot/2.1 (+http://www.google.com/bot.html'
            }

            try:
                response = requests.get(url, headers=headers, verify=True, timeout=60)  # exploit-db.com takes a while to load sometimes

                if response.status_code == 200:
                    page = response.text

                    # Using beautiful soup to drill down to the actual Google dork
                    soup = BeautifulSoup(page, "html.parser")
                    table = soup.find_all('table')[0]
                    column = table.find_all('td')[2]
                    dork = column.find_all('a')[0].contents[0]

                    # Clean up string by removing '\n' characters and spaces.
                    # https://www.exploit-db.com/ghdb/9/
                    # '\n                intitle:index.of .bash_history            ' --> intitle:index.of .bash_history
                    dork = " ".join(dork.split())

                    try:
                        print("[+] Retrieving dork {0}: {1}".format(dork_number, dork))
                        ghdb.dorks.append(dork)

                    except:
                        print("[-] Dork number {0} failed: {1}".format(dork_number, dork))

                else:
                    print("Could not access {0}. HTTP status code: {1}".format(url, response.status_code))

            except:
                print("[-] Random error with dork number {0}.".format(dork_number))

            ghdb.queue.task_done()


class GHDBCollector:

    def __init__(self, min_dork_number, max_dork_number, save_directory, save_dorks, number_of_threads):
        self.min_dork_number = min_dork_number
        self.max_dork_number = max_dork_number
        self.save_directory = save_directory
        self.save_dorks = save_dorks
        self.dorks = []

        # Create queue and specify the number of worker threads.
        self.queue = queue.Queue()
        self.number_of_threads = number_of_threads

    def go(self):
        # Kickoff the threadpool.
        for i in range(self.number_of_threads):
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
            google_dork_file = 'google_dorks_{0}.txt'.format(get_timestamp())
            with open(os.path.join(self.save_directory, google_dork_file), 'a') as fh:
                for dork in self.dorks:
                    fh.write(dork + "\n")

        print("[*] Total Google dorks retrieved: {0}".format(len(self.dorks)))


def get_timestamp():
    now = time.localtime()
    timestamp = time.strftime('%Y%m%d_%H%M%S', now)
    return timestamp


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='GHDB Scraper - Retrieve the Google Hacking Database dorks from exploit-db.com')
    parser.add_argument('-n', dest='min_dork_number', action='store', type=int, default=5, help='Minimum Google dork number to start at (Default: 5).')
    parser.add_argument('-x', dest='max_dork_number', action='store', type=int, default=5000, help='Maximum Google dork number, not the total, to retrieve (Default: 5000).  It is currently around 3800.  There is no logic in this script to determine when it has reached the end.')
    parser.add_argument('-d', dest='save_directory', action='store', default=os.getcwd(), help='Directory to save downloaded files (Default: cwd, ".")')
    parser.add_argument('-s', dest='save_dorks', action='store_true', default=False, help='Save the Google dorks to google_dorks_<TIMESTAMP>.txt file')
    parser.add_argument('-t', dest='number_of_threads', action='store', type=int, default=3, help='Number of search threads (Default: 3)')

    args = parser.parse_args()

    if args.save_directory:
        print("[*] Dork file will be saved here: {0}".format(args.save_directory))
        if not os.path.exists(args.save_directory):
            print("[+] Creating folder: " + args.save_directory)
            os.mkdir(args.save_directory)
    if (args.min_dork_number < 5):
        print("[!] Search Google Dork MIN must be 5 or greater (-n)")
        sys.exit()
    if (args.max_dork_number < 5):
        print("[!] Search Google Dork MAX must be 5 or greater (-x)")
        sys.exit()
    if args.number_of_threads < 0:
        print("[!] Number of threads (-n) must be greater than 0")
        sys.exit()

    print("[*] Initiation timestamp: {0}".format(get_timestamp()))
    ghdb = GHDBCollector(**vars(args))
    ghdb.go()
    print("[*] Completion timestamp: {0}".format(get_timestamp()))

    print("[+] Done!")
