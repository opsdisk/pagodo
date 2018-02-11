#### Introduction

The goal of this project was to develop a passive Google dork script to collect potentially vulnerable web pages and applications on the Internet.  There are 2 parts.  The first is **ghdb\_scraper.py** that retrieves Google Dorks and the second portion is **pagodo.py** that leverages the information gathered by **ghdb\_scraper.py**.

To my knowledge, AeonDave beat **pagodo.py** to market with the similar "doork" tool (https://github.com/AeonDave/doork), so definitely check that one out too.  I have been working sporadically on the scripts for a couple months and finally got them to a publishable point.

#### tl;dr

The code can be found here: https://github.com/opsdisk/pagodo

#### What are Google Dorks?

The awesome folks at Offensive Security maintain the Google Hacking Database (GHDB) found here: https://www.exploit-db.com/google-hacking-database.  It is a collection of Google searches, called dorks, that can be used to find potentially vulnerable boxes or other juicy info that is picked up by Google's search bots.  

#### Installation

Clone the git repository and install the requirements
```
pip install -r requirements.txt
```

#### ghdb_scraper.py

To start off, **pagodo.py** needs a list of all the current Google dorks.  Unfortunately, the entire database cannot be easily downloaded.  A couple of older projects did this, but the code was slightly stale and it wasn't multi-threaded...so collecting ~3800 Google Dorks would take a long time.  **ghdb_scraper.py** is the resulting Python script.

The primary inspiration was taken from dustyfresh's ghdb-scrape (https://github.com/dustyfresh/ghdb-scrape).  Code was also reused from **aquabot** (https://github.com/opsdisk/aquabot) and the rewrite of **metagoofil** (https://github.com/opsdisk/metagoofil).

The Google dorks start at number 5 and go up to 4318 as of this writing, but that does not mean there is a corresponding Google dork for each number.  An example URL with the Google dork specified is: https://www.exploit-db.com/ghdb/11/  There really isn't any rhyme or reason, so putting a large arbitrary max like 5000 would cover you.  The script is not smart enough to detect the end of the Google dorks.

#### ghdb_scraper.py Execution Flow

The flow of execution is pretty simple:

* Fill a queue with Google dork numbers to retrieve based off a range
* Worker threads retrieve the dork number from the queue, retrieve the page using urllib2, then process the page to extract the Google dork using the BeautifulSoup HTML parsing library
* Print the results to the screen and optionally save them to a file (to be used by **pagodo.py** for example)

The website doesn't block requests using 3 threads, but did for 8...your mileage may vary.

#### ghdb_scraper.py Switches

The script's switches are self explanatory:

    -n MINDORKNUM     Minimum Google dork number to start at (Default: 5).
    -x MAXDORKNUM     Maximum Google dork number, not the total, to retrieve
                      (Default: 5000). It is currently around 3800. There is no
                      logic in this script to determine when it has reached the
                      end.
    -d SAVEDIRECTORY  Directory to save downloaded files (Default: cwd, ".")
    -s                Save the Google dorks to google_dorks_<TIMESTAMP>.txt file
    -t NUMTHREADS     Number of search threads (Default: 3)


To run it

    python ghdb_scraper.py -n 5 -x 3785 -s -t 3

#### pagodo.py

Now that a file with the most recent Google dorks exists, it can be fed into **pagodo.py** using the `-g` switch to start collecting potentially vulnerable public applications.  **pagodo.py** leverages the `google` python library to search Google for sites with the Google dork, such as:

    intitle:"ListMail Login" admin -demo

The `-d` switch can be used to specify a domain and functions as the Google search operator:

    site:example.com  

Performing ~3800 search requests to Google as fast as possible will simply not work.  Google will rightfully detect it as a bot and block your IP for a set period of time.  In order to make the search queries appear more human, a couple of enhancements have been made.  A pull request was made and accepted by the maintainer of the Python `google` module to allow for User-Agent randomization in the Google search queries.  This feature is available in 1.9.3 (https://pypi.python.org/pypi/google) and allows you to randomize the different user agents used for each search.  This emulates the different browsers used in a large corporate environment.

The second enhancement focuses on randomizing the time between search queries.  A minimum delay is specified using the `-e` option (default is 30.0 seconds) and a jitter factor is used to add time on to the minimum delay number. A list of 50 jitter times is created and one is randomly appended to the minimum delay time for each Google dork search.  

```python
# Create an array of jitter values to add to delay, favoring longer search times.
self.jitter = numpy.random.uniform(low=self.delay, high=jitter * self.delay, size=(50,))
```

Latter in the script, a random time is selected from the jitter array and added to the delay.

```python
pause_time = self.delay + random.choice(self.jitter)
```

Experiment with the values, but the defaults successfully worked without Google blocking my IP.  Note that it could take a few hours/days to run so be sure you have the time...the first successful run took over 48 hours.

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

#### Future Work

Future work includes grabbing the Google dork description to provide some context around the dork and why it is in the Google Hacking Database.

#### Conclusion

All of the code can be found on the Opsdisk Github repository here: https://github.com/opsdisk/pagodo.  Comments, suggestions, and improvements are always welcome.  Be sure to follow [@opsdisk](https://twitter.com/opsdisk) on Twitter for the latest updates.
