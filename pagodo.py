#!/usr/bin/env python
# GPL v 2.0 License
# Opsdisk LLC | opsdisk.com
from __future__ import print_function

import argparse
import google  # https://pypi.python.org/pypi/google
import numpy
import os
import random
import sys
import time


# Rewritting google.get_page to randomize User-Agent
'''
def new_get_page(url):
    """
    Request the given URL and return the response page, using the cookie jar.

    @type  url: str
    @param url: URL to retrieve.

    @rtype:  str
    @return: Web page retrieved for the given URL.

    @raise IOError: An exception is raised on error.
    @raise urllib2.URLError: An exception is raised on error.
    @raise urllib2.HTTPError: An exception is raised on error.
    """
    request = Request(url)
    userAgent = random.choice(pgd.randomUserAgents)
    print("[*] User-Agent", userAgent)
    request.add_header('User-Agent', userAgent)  #'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0)')
    cookie_jar.add_cookie_header(request)
    response = urlopen(request)
    cookie_jar.extract_cookies(response, request)
    html = response.read()
    response.close()
    cookie_jar.save()
    return html

get_page = new_get_page
'''

class Pagodo:

    def __init__(self, domain, googleDorks, searchMax, saveLinks, delay):
        self.domain = domain
        self.googleDorks = open(googleDorks, 'r')
        self.searchMax = searchMax
        self.saveLinks = saveLinks
        if saveLinks:
            self.logFile = 'pagodo_results_' + get_timestamp() + '.txt'
        self.delay = delay
        self.totalDorks = 0

        #with open('user_agents.txt') as fp:
        #    self.randomUserAgents = fp.readlines()

        # Create an array of jitter values to add to delay, favoring longer search times.
        self.jitter = numpy.random.uniform(low=-.2 * self.delay, high=2 * self.delay, size=(50,))
        
    def go(self):
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
                print("[*] Searching for Google dork [ " + query + " ] and waiting " + str(pauseTime) + " seconds between searches")                
                
                for url in google.search(query, start=0, stop=self.searchMax, num=100, pause=pauseTime, extra_params={'filter': '0'}):
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
        
        self.googleDorks.close
        print("[*] Total sites found with Google dorks: " + str(self.totalDorks))


def get_timestamp():
    now = time.localtime()
    timestamp = time.strftime('%Y%m%d_%H%M%S', now)
    return timestamp                   

 
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Passive Google Dork - pagodo')
    parser.add_argument('-d', dest='domain', action='store', required=False, help='Domain to search for Google dork hits.')
    parser.add_argument('-g', dest='googleDorks', action='store', required=True, help='File containing Google dorks, 1 per line.')
    parser.add_argument('-l', dest='searchMax', action='store', type=int, default=100, help='Maximum results to search (default 100).')
    parser.add_argument('-s', dest='saveLinks', action='store_true', default=False, help='Save the html links to pagodo_results__<TIMESTAMP>.txt file.')
    parser.add_argument('-e', dest='delay', action='store', type=float, default=10.0, help='Delay (in seconds) between searches.  If it\'s too small Google may block your IP, too big and your search may take a while. Default: 10.0')

    args = parser.parse_args()

    if not os.path.exists(args.googleDorks):
        print("[!] Specify a valid file containing Google dorks with -g")
        sys.exit()
    if args.delay < 0:
        print("[!] Delay must be greater than 0")
        sys.exit()

    #print(vars(args))
    pgd = Pagodo(**vars(args))
    pgd.go()

    print("[+] Done!")
