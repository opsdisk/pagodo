# PaGoDo

## Introduction

The goal of this project was to develop a passive Google dork script to collect potentially vulnerable web pages and applications on the Internet.  There are 2 parts.  The first is `ghdb_scraper.py` that retrieves Google Dorks and the second portion is `pagodo.py` that leverages the information gathered by `ghdb_scraper.py`.

## What are Google Dorks?

The awesome folks at Offensive Security maintain the Google Hacking Database (GHDB) found here: <https://www.exploit-db.com/google-hacking-database>.  It is a collection of Google searches, called dorks, that can be used to find potentially vulnerable boxes or other juicy info that is picked up by Google's search bots.  

## Installation

Scripts are written for Python 3.6+.  Clone the git repository and install the requirements.

```bash
git clone git@github.com:opsdisk/pagodo.git
cd pagodo
virtualenv -p python3 .venv  # If using a virtual environment.
source .venv/bin/activate  # If using a virtual environment.
pip3 install -r requirements.txt
```

## ghdb_scraper.py

To start off, `pagodo.py` needs a list of all the current Google dorks.  A datetimestamped file with the Google dorks is also provded in the repo.  Fortunately, the entire database can be pulled back with 1 GET request using `ghdb_scraper.py`.  You can dump the individual dorks to a text file, or the entire json blob if you want more contextual data about the dork.

To run it:

```bash
python3 ghdb_scraper.py -j -s
```

## pagodo.py

Now that a file with the most recent Google dorks exists, it can be fed into `pagodo.py` using the `-g` switch to start collecting potentially vulnerable public applications.  `pagodo.py` leverages the `google` python library to search Google for sites with the Google dork, such as:

    intitle:"ListMail Login" admin -demo

The `-d` switch can be used to specify a domain and functions as the Google search operator:

    site:example.com  

Performing ~4600 search requests to Google as fast as possible will simply not work.  Google will rightfully detect it as a bot and block your IP for a set period of time.  In order to make the search queries appear more human, a couple of enhancements have been made.  A pull request was made and accepted by the maintainer of the Python `google` module to allow for User-Agent randomization in the Google search queries.  This feature is available in [1.9.3](https://pypi.python.org/pypi/google) and allows you to randomize the different user agents used for each search.  This emulates the different browsers used in a large corporate environment.

The second enhancement focuses on randomizing the time between search queries.  A minimum delay is specified using the `-e` option and a jitter factor is used to add time on to the minimum delay number. A list of 50 jitter times is created and one is randomly appended to the minimum delay time for each Google dork search.

```python
# Create an array of jitter values to add to delay, favoring longer search times.
self.jitter = numpy.random.uniform(low=self.delay, high=jitter * self.delay, size=(50,))
```

Latter in the script, a random time is selected from the jitter array and added to the delay.

```python
pause_time = self.delay + random.choice(self.jitter)
```

Experiment with the values, but the defaults successfully worked without Google blocking my IP.  Note that it could take a few days (3 on average) to run so be sure you have the time.

To run it:

```bash
python3 pagodo.py -d example.com -g dorks.txt -l 50 -s -e 35.0 -j 1.1
```

## Conclusion

Comments, suggestions, and improvements are always welcome.  Be sure to follow [@opsdisk](https://twitter.com/opsdisk) on Twitter for the latest updates.
