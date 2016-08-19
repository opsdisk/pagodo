#### Introduction

The code can be found here: https://github.com/opsdisk/pagodo

The goal of this project was to develop a passive Google dorking script to collect potentially vulnerable web pages and applications on the Internet.  I was doing some work for an organization that wanted to see what Google was able to scrape about their public applications.  

There are 2 parts.  The first is **ghdb\_scraper.py** that retrieves Google Dorks and the second portion is **pagodo.py** that leverages the information gathered by **ghdb_scraper.py**.

To my knowledge, AeonDave beat **pagodo.py** to market with the similar "doork" tool (https://github.com/AeonDave/doork), so definitely check that one out too.  I'd been working sporadically on the scripts for a couple months and finally got it to where I want to publish it.

#### What are Google Dorks?

The awesome folks at Offensive Security maintain the Google Hacking Database (GHDB) found here: https://www.exploit-db.com/google-hacking-database/

It is a collection of Google searches that can be used to find potentially vulnerable boxes or other juicy info that is picked up by Google's search bots.  

#### ghdb_scraper.py

I started work on **pagodo.py** and needed a list of all the current Google Dorks.  Unfortunately, the entire database cannot be easily downloaded.  A couple of older projects did this, but the code was slightly stale and it wasn't multi-threaded...so collecting ~3800 Google Dorks would take a long time.  **ghdb_scraper.py** is the resulting Python script.

The primary inspiration was taken from dustyfresh's ghdb-scrape (https://github.com/dustyfresh/ghdb-scrape).  Code was also reused from **aquabot** (https://github.com/opsdisk/aquabot) and my rewrite of **metagoofil** (https://github.com/opsdisk/metagoofil).

The Google dorks start at number 5 and go up to 4281 as of this writing, but that does not mean there is a corresponding Google dork for that number.  An example URL with the Google dork specified is: https://www.exploit-db.com/ghdb/11/  There really isn't any rhyme or reason, so putting a large arbitrary max like 5000 would cover you.  The script is not smart enough to detect the end of the Google dorks.

#### ghdb_scraper.py Execution Flow

The flow of execution is pretty simple:

* Fill a queue with Google dork numbers to retrieve based off a range
* Worker threads retrieve the dork number from the queue, retrieve the page using urllib2, then process the page to extract the Google dork using the BeautifulSoup HTML parsing library
* Print the results to the screen and optionally save them to a file (to be used by **pagodo.py** for example)

The website didn't block requests using 3 threads, but did for 8.  Your mileage may vary.

#### ghdb_scraper.py Switches

The script's switches are self explanatory:
      
    -n MINDORKNUM     Minimum Google dork number to start at (default is 5).
    -x MAXDORKNUM     Maximum Google dork number, not the total, to retrieve
                      (default 100). It is currently around 3800. There is no
                      logic in this script to determine when it has reached the
                      end.
    -o SAVEDIRECTORY  Directory to save downloaded files (default is cwd, ".")
    -f                Save the Google dorks to google_dorks_<TIMESTAMP>.txt file
    -t NUMTHREADS     Number of search threads (default is 3)

To run it

    python ghdb_scraper.py -n 5 -x 3785 -f -t 3

#### pagodo.py
Now that we have a file with the most recent Google dorks, it can be fed into **pagodo.py* using the `-g` switch to start collecting potentially vulnerable public applications.  **pagodo.py** leverages the `google` python library to search Google for sites with the Google Dork, such as:

    intitle:"ListMail Login" admin -demo

A `-d` switch can be used to specify a domain and functions as the Google search operator:
`site:example.com`.  

Performing ~3800 search requests to Google as fast as possible will simply not work.  They are able to detect bots and will block your IP for a set period of time.  In order to make the search queries appear more human, a couple of enhancements have been made.  A pull request was made and accepted by the maintainer of the Python `google` module to allow for User-Agent randomization in the Google search queries.  This feature is available in 1.9.3 (https://pypi.python.org/pypi/google) and allows you to randomize the different user agents used for each search.  This emulates the different browsers used in a large corporate environment.

The second enhancement focuses on randomizing the time between search queries.  A minimum delay is specified using the `-e` option (default is 30.0 seconds) and a jitter factor is used to add time on to the minimum delay number. A list of 50 times is created and one is randomly appended to the minimum delay time for each Google dork search.  Experiment with the values, but the defaults worked for me.  Note that it could take a few hours to run so be sure you have the time. 

```python
# Create an array of jitter values to add to delay, favoring longer search times.
self.jitter = numpy.random.uniform(low=self.delay, high=jitter * self.delay, size=(50,))
```

Latter in the script, a random time is selected from the jitter array and added to the dealy.

```python
pauseTime = self.delay + random.choice(self.jitter)
```

#### pagodo.py Switches
The script's switches are self explanatory:
      
    -d DOMAIN       Domain to search for Google dork hits.
    -g GOOGLEDORKS  File containing Google dorks, 1 per line.
    -j JITTER       jitter factor (multipled times delay value) added to
                    randomize lookups times. Default: 1.50
    -l SEARCHMAX    Maximum results to search (default 100).
    -s              Save the html links to pagodo_results__<TIMESTAMP>.txt file.
    -e DELAY        Minimum delay (in seconds) between searches...jitter (up to
                    [jitter X delay] value) is added to this value to randomize
                    lookups. If it's too small Google may block your IP, too big
                    and your search may take a while. Default: 30.0

To run it

    python pagodo.py -d example.com -g dorks.txt -l 50 -s -e 35.0 -j 1.1

#### Code
The code can be found here: https://github.com/opsdisk/pagodo

#### Conclusion
All of the code can be found on the Opsdisk Github repository here: https://github.com/opsdisk/pagodo.  Comments, suggestions, and improvements are always welcome.  Be sure to follow [@opsdisk](https://twitter.com/opsdisk) on Twitter for the latest updates. 
 