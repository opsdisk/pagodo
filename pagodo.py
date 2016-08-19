#!/usr/bin/env python
# GPL v 2.0 License
# Opsdisk LLC | opsdisk.com
from __future__ import print_function

import argparse
import google  # google >= 1.9.3, https://pypi.python.org/pypi/google
import numpy
import os
import random
import sys
import time


class Pagodo:

    def __init__(self, domain, googleDorks, searchMax, saveLinks, delay, jitter):
        self.domain = domain
        with open(googleDorks) as self.fp:
            self.googleDorks = self.fp.read().splitlines()
        self.searchMax = searchMax
        self.saveLinks = saveLinks
        if saveLinks:
            self.logFile = 'pagodo_results_' + get_timestamp() + '.txt'
        self.delay = delay
        
        # Create an array of jitter values to add to delay, favoring longer search times.
        self.jitter = numpy.random.uniform(low=self.delay, high=jitter * self.delay, size=(50,))
        
        self.totalDorks = 0

    def go(self):
        i = 1
        for dork in self.googleDorks:
            try:
                dork = dork.strip()
                self.links = []  # Stores URLs with files, clear out for each dork

                # Search for the links to collect
                if self.domain:
                    query = dork + " site:" + self.domain
                else:
                    query = dork
                
                pauseTime = self.delay + random.choice(self.jitter)
                print("[*] Search ( " + str(i) + " / " + str(len(self.googleDorks)) + " ) for Google dork [ " + query + " ] and waiting " + str(pauseTime) + " seconds between searches")                
                
                for url in google.search(query, start=0, stop=self.searchMax, num=100, pause=pauseTime, extra_params={'filter': '0'}, user_agent=google.get_random_user_agent()):
                    self.links.append(url)
                
                # Since google.search method retreives URLs in batches of 100, ensure the file list only contains the requested amount
                if len(self.links) > self.searchMax:
                    self.links = self.links[:-(len(self.links) - self.searchMax)] 
                            
                print("[*] Results: " + str(len(self.links)) + " sites found for Google dork: " + dork)
                for foundDork in self.links:
                    print(foundDork)
                
                self.totalDorks += len(self.links)

                # Only save links with valid results to an output file
                if self.saveLinks and (self.links):
                    f = open(self.logFile, 'a')
                    f.write('#: ' + dork + "\n")
                    for link in self.links:
                        f.write(link + "\n")
                    f.write("=" * 50 + "\n")
                    f.close

            except:
                print("[-] ERROR with dork: " + dork)
            
            i += 1

        self.fp.close
        print("[*] Total dorks found: " + str(self.totalDorks))


def get_timestamp():
    now = time.localtime()
    timestamp = time.strftime('%Y%m%d_%H%M%S', now)
    return timestamp                   

 
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Passive Google Dork - pagodo')
    parser.add_argument('-d', dest='domain', action='store', required=False, help='Domain to search for Google dork hits.')
    parser.add_argument('-g', dest='googleDorks', action='store', required=True, help='File containing Google dorks, 1 per line.')
    parser.add_argument('-j', dest='jitter', action='store', type=float, default=.75, help='jitter factor (multipled times delay value) added to randomize lookups times. Default: 1.50')
    parser.add_argument('-l', dest='searchMax', action='store', type=int, default=100, help='Maximum results to search (default 100).')
    parser.add_argument('-s', dest='saveLinks', action='store_true', default=False, help='Save the html links to pagodo_results__<TIMESTAMP>.txt file.')
    parser.add_argument('-e', dest='delay', action='store', type=float, default=30.0, help='Minimum delay (in seconds) between searches...jitter (up to [jitter X delay] value) is added to this value to randomize lookups. If it\'s too small Google may block your IP, too big and your search may take a while. Default: 30.0')

    args = parser.parse_args()

    if not os.path.exists(args.googleDorks):
        print("[!] Specify a valid file containing Google dorks with -g")
        sys.exit()
    if args.delay < 0:
        print("[!] Delay must be greater than 0")
        sys.exit()
    '''if args.jitter < 0:
        print("[!] Jitter must be greater than 0")
        sys.exit()'''

    #print(vars(args))
    print("[*] Initiation timestamp: " + get_timestamp())
    pgd = Pagodo(**vars(args))
    pgd.go()
    print("[*] Completion timestamp: " + get_timestamp())

    print("[+] Done!")
