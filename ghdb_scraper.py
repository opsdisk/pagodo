#!/usr/bin/env python
# GPL v 2.0 License
# Opsdisk LLC | opsdisk.com
from __future__ import print_function

import argparse
import os
import Queue
import sys
import threading
import time
import urllib2
from bs4 import BeautifulSoup


class Worker(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        
    def run(self):
        while True:          
            # Grab URL off the queue and build the request
            dorkNum = ghdb.queue.get()
            url = 'https://www.exploit-db.com/ghdb/' + str(dorkNum) + '/'
            request = urllib2.Request(url)
            request.add_header('User-Agent', 'Googlebot/2.1 (+http://www.google.com/bot.html')

            try:
                page = urllib2.urlopen(request, timeout=30)  # exploit-db.com takes a while to load sometimes
                
                # Using beautiful soup to drill down to the actual Google dork                
                soup = BeautifulSoup(page.read())
                table = soup.find_all('table')[0]
                column = table.find_all('td')[1]
                dork = column.contents[2].contents[0]
                           
                try:
                    print("[+] Retrieving dork " + str(dorkNum) + ": " + dork)
                    ghdb.dorks.append(dork)
       
                except:
                    print("[-] Dork number " + str(dorkNum) + " failed: " + dork)
                 
                page.close()  
            
            except:
                print("[-] Random error with dork number " + str(dorkNum))
            
            ghdb.queue.task_done()


class GHDBCollector:

    def __init__(self, minDorkNum, maxDorkNum, saveDirectory, saveDorks, numThreads):
        self.minDorkNum = minDorkNum
        self.maxDorkNum = maxDorkNum
        self.saveDirectory = saveDirectory
        self.saveDorks = saveDorks 
        self.dorks = []

        # Create queue and specify the number of worker threads.
        self.queue = Queue.Queue() 
        self.numThreads = numThreads

    def go(self):
        # Kickoff the threadpool.
        for i in range(self.numThreads):
            thread = Worker()
            thread.daemon = True
            thread.start()

        # Populate the queue with the Google dork range.
        for dorkNum in range(self.minDorkNum, self.maxDorkNum + 1):
            self.queue.put(dorkNum)
        self.queue.join()

        print("-" * 50)
        for dork in self.dorks:
            print(dork)
        print("-" * 50)

        if self.saveDorks:
            self.f = open(self.saveDirectory + '/' + 'google_dorks_' + get_timestamp() + '.txt', 'a')
            for dork in self.dorks:
                self.f.write(dork.encode('utf-8') + "\n")
            self.f.close()

        print("[*] Total Google dorks retrieved: " + str(len(self.dorks)))
        

def get_timestamp():
    now = time.localtime()
    timestamp = time.strftime('%Y%m%d_%H%M%S', now)
    return timestamp
      

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='GHDB Scraper - Retrieve the Google Hacking Database dorks from exploit-db.com')
    parser.add_argument('-n', dest='minDorkNum', action='store', type=int, default=5, help='Minimum Google dork number to start at (Default: 5).')
    parser.add_argument('-x', dest='maxDorkNum', action='store', type=int, default=5000, help='Maximum Google dork number, not the total, to retrieve (Default: 5000).  It is currently around 3800.  There is no logic in this script to determine when it has reached the end.')
    parser.add_argument('-d', dest='saveDirectory', action='store', default=os.getcwd(), help='Directory to save downloaded files (Default: cwd, ".")')
    parser.add_argument('-s', dest='saveDorks', action='store_true', default=False, help='Save the Google dorks to google_dorks_<TIMESTAMP>.txt file')
    parser.add_argument('-t', dest='numThreads', action='store', type=int, default=3, help='Number of search threads (Default: 3)')

    args = parser.parse_args()

    if args.saveDirectory:
        print("[*] Dork file will be saved here: " + args.saveDirectory)
        if not os.path.exists(args.saveDirectory):
            print("[+] Creating folder: " + args.saveDirectory)
            os.mkdir(args.saveDirectory)
    if (args.minDorkNum < 5):
        print("[!] Search Google Dork MIN must be 5 or greater (-n)")
        sys.exit()
    if (args.maxDorkNum < 5):
        print("[!] Search Google Dork MAX must be 5 or greater (-x)")
        sys.exit()
    if args.numThreads < 0:
        print("[!] Number of threads (-n) must be greater than 0")
        sys.exit()

    #print(vars(args))
    print("[*] Initiation timestamp: " + get_timestamp())
    ghdb = GHDBCollector(**vars(args))
    ghdb.go()
    print("[*] Completion timestamp: " + get_timestamp())

    print("[+] Done!")
