#!/usr/bin/env python
# GPL v 3.0 License
# Opsdisk LLC | opsdisk.com
from __future__ import print_function

import argparse
import os
import random
import sys
import time

import numpy

# google == 2.0.1, module author changed import name
# https://github.com/MarioVilas/googlesearch/commit/92309f4f23a6334a83c045f7c51f87b904e7d61d
import googlesearch


class Pagodo:

    def __init__(self, domain, google_dorks, search_max, save_links, delay, jitter, randomize_user_agent):
        self.domain = domain
        with open(google_dorks) as self.fp:
            self.google_dorks = self.fp.read().splitlines()
        self.search_max = search_max
        self.save_links = save_links
        if save_links:
            self.log_file = 'pagodo_results_{0}.txt'.format(get_timestamp())
        self.delay = delay

        # Create an array of jitter values to add to delay, favoring longer search times.
        self.jitter = numpy.random.uniform(low=self.delay, high=jitter * self.delay, size=(50,))

        self.randomize_user_agent = randomize_user_agent
        # Populate a list of random User-Agents
        if self.randomize_user_agent is True:
            with open('user_agents.txt') as fp:
                self.random_user_agents = fp.readlines()

        self.total_dorks = 0

    def go(self):
        i = 1
        for dork in self.google_dorks:
            try:
                dork = dork.strip()
                self.links = []  # Stores URLs with files, clear out for each dork.

                # Search for the links to collect.
                if self.domain:
                    query = "{0} site:{1}".format(dork, self.domain)
                else:
                    query = dork

                pause_time = self.delay + random.choice(self.jitter)

                # Determine User-Agent based off user preference.
                if self.randomize_user_agent is False:
                    user_agent = None
                else:
                    user_agent = random.choice(self.random_user_agents).strip()

                print("[*] Search ( {0} / {1} ) for Google dork [ {2} ] and waiting {3} seconds between searches using User-Agent '{4}'".format(i, len(self.google_dorks), query, pause_time, user_agent))

                for url in googlesearch.search(query, start=0, stop=self.search_max, num=100, pause=pause_time, extra_params={'filter': '0'}, user_agent=user_agent):
                    self.links.append(url)

                # Since googlesearch.search method retreives URLs in batches of 100, ensure the file list only contains the requested amount.
                if len(self.links) > self.search_max:
                    self.links = self.links[:-(len(self.links) - self.search_max)]

                print("[*] Results: {0} sites found for Google dork: {1}".format(len(self.links), dork))
                for foundDork in self.links:
                    print(foundDork)

                self.total_dorks += len(self.links)

                # Only save links with valid results to an output file.
                if self.save_links and (self.links):
                    with open(self.log_file, 'a') as fh:
                        fh.write('#: ' + dork + "\n")
                        for link in self.links:
                            fh.write(link + "\n")
                        fh.write("=" * 50 + "\n")

            except KeyboardInterrupt:
                sys.exit(0)

            except Exception as e:
                print("[-] ERROR with dork: {0}".format(dork))
                print("[-] EXCEPTION: {0}".format(e))
                sys.exit(0)

            i += 1

        self.fp.close
        print("[*] Total dorks found: {0}".format(self.total_dorks))


def get_timestamp():
    now = time.localtime()
    timestamp = time.strftime('%Y%m%d_%H%M%S', now)
    return timestamp


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Passive Google Dork - pagodo')
    parser.add_argument('-d', dest='domain', action='store', required=False, help='Domain to search for Google dork hits.')
    parser.add_argument('-g', dest='google_dorks', action='store', required=True, help='File containing Google dorks, 1 per line.')
    parser.add_argument('-j', dest='jitter', action='store', type=float, default=.75, help='jitter factor (multipled times delay value) added to randomize lookups times.  DEFAULT: 1.50')
    parser.add_argument('-l', dest='search_max', action='store', type=int, default=100, help='Maximum results to search.  DEFAULT 100.')
    parser.add_argument('-s', dest='save_links', action='store_true', default=False, help='Save the html links to pagodo_results__<TIMESTAMP>.txt file.')
    parser.add_argument('-e', dest='delay', action='store', type=float, default=30.0, help='Minimum delay (in seconds) between searches...jitter (up to [jitter X delay] value) is added to this value to randomize lookups. If it\'s too small Google may block your IP, too big and your search may take a while.  DEFAULT: 30.0')
    parser.add_argument('-u', dest='randomize_user_agent', action='store_false', required=False, default=True, help='Disable randomizing User-Agent for Google searches.  Not recommended.')

    args = parser.parse_args()

    if not os.path.exists(args.google_dorks):
        print("[!] Specify a valid file containing Google dorks with -g")
        sys.exit()
    if args.delay < 0:
        print("[!] Delay must be greater than 0")
        sys.exit()

    print("[*] Initiation timestamp: {0}".format(get_timestamp()))
    pgd = Pagodo(**vars(args))
    pgd.go()
    print("[*] Completion timestamp: {0}".format(get_timestamp()))

    print("[+] Done!")
