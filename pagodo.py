#!/usr/bin/env python
# GPL v 2.0 License
# Opsdisk LLC | opsdisk.com
from __future__ import print_function

import argparse
import google  # https://pypi.python.org/pypi/google
import Queue
import sys
import time


class Pagodo:

    def __init__(self, domain, googleDorks, searchMax, saveLinks, delay, urlTimeout, numThreads):  # saveDirectory, downloadFileLimit, downloadFiles
        self.domain = domain
        self.googleDorks = open(googleDorks, 'r')
        self.searchMax = searchMax
        #self.downloadFileLimit = downloadFileLimit
        #self.maxDownloadSize = maxDownloadSize
        #self.saveDirectory = saveDirectory
        #self.downloadFiles = downloadFiles
        self.saveLinks = saveLinks
        if saveLinks:
            self.logFile = 'pagodo_results_' + get_timestamp() + '.txt'
        self.delay = delay
        #self.totalBytes = 0
        self.urlTimeout = urlTimeout
        
        # Create queue and specify the number of worker threads.
        self.queue = Queue.Queue() 
        self.numThreads = numThreads

    def go(self):
        for dork in self.googleDorks:
            dork = dork.strip()

            self.links = []  # Stores URLs with files, clear out for each dork

            # Search for the links to collect
            print("[*] Searching for Google dork [ " + dork + " ] and waiting " + str(self.delay) + " seconds between searches")
            query = dork + " site:" + self.domain
            for url in google.search(query, start=0, stop=self.searchMax, num=100, pause=self.delay):
                self.links.append(url)
            
            # Since google.search method retreives URLs in batches of 100, ensure the file list only contains the requested amount
            if len(self.links) > self.searchMax:
                self.links = self.links[:-(len(self.links) - self.searchMax)] 
                        
            print("[*] Results: " + str(len(self.links)) + " sites found for Google dork: " + dork)
            for foundDork in self.links:
                print(foundDork)
            
            # Only save links with valid results to an output file
            if self.saveLinks and (self.links):
                f = open(self.logFile, 'a')
                f.write(dork + "\n")
                for link in self.links:
                    f.write(link + "\n")
                f.write("=" * 50 + "\n")
                f.close
        
        self.googleDorks.close


def get_timestamp():
    now = time.localtime()
    timestamp = time.strftime('%Y%m%d_%H%M%S', now)
    return timestamp                   

 
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Passive Google Dork - pagodo')
    parser.add_argument('-d', dest='domain', action='store', required=True, help='Domain to search')
    parser.add_argument('-g', dest='googleDorks', action='store', required=True, help='File containing Google dorks, 1 per line.')
    parser.add_argument('-l', dest='searchMax', action='store', type=int, default=100, help='Maximum results to search (default 100)')
    parser.add_argument('-s', dest='saveLinks', action='store_true', default=False, help='Save the html links to pagodo_results__<TIMESTAMP>.txt file')
    parser.add_argument('-e', dest='delay', action='store', type=float, default=7.0, help='Delay (in seconds) between searches.  If it\'s too small Google may block your IP, too big and your search may take a while.')
    #parser.add_argument('-i', dest='urlTimeout', action='store', type=int, default=5, help='Number of seconds to wait before timeout for unreachable/stale pages (default 5)')
    parser.add_argument('-r', dest='numThreads', action='store', type=int, default=8, help='Number of search threads (default is 8)')

    args = parser.parse_args()

    if not args.domain:
        print("[!] Specify a domain with -d")
        sys.exit()
    if not args.googleDorks:
        print("[!] Specify file containing Google dorks with -g")
        sys.exit()
    if args.delay < 0:
        print("[!] Delay must be greater than 0")
        sys.exit()
    if args.urlTimeout < 0:
        print("[!] URL timeout (-i) must be greater than 0")
        sys.exit()
    if args.numThreads < 0:
        print("[!] Number of threads (-n) must be greater than 0")
        sys.exit()

    pgd = Pagodo(**vars(args))
    pgd.go()

    print("[+] Done!")
