# -*- coding: utf-8 -*-
"""
Created on 01/20/2019
NSC - AD440 CLOUD PRACTICIUM
@author: Michael Leon

"""
import urllib.request
import re
import os
import json
import time
from bs4 import BeautifulSoup
import time
from dateutil.parser import parse
from datetime import datetime
import boto3

# This script scrapes a website and pulls specific data.
FOUND_LIST = []
OUTPUT = {}
SOUP = []
FIRST_PAGE = True
EVENT_BRITE = "https://www.eventbrite.com/d/wa--seattle/disability/?page=1"
#s3 = boto3.resource('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

def open_url(url):
    global FIRST_PAGE
    # Function opens a url, parses it with Beautifulsoup
    # Finds relevant links and adds them to the global QUEUE
    # Foundlist used to avoid duplicates
    try:
        response = urllib.request.urlopen(url)
        soup = BeautifulSoup(response, "html.parser")
        print("Opening " + url + "; success" + "\n")
    except:
        print("Opening " + url + "; failed" + "\n")
    #Find all links and add them to the queue and found
    first_row = True        
    for row in soup.findAll("a", {"href" : True}):
        try:
            if ("https" in row["href"] and
                    ("seattle" in row["href"] or "/e/" in row["href"]) and
                    "login" not in row["href"]):            
                if first_row and (row["href"] == FOUND_LIST[0]) :
                    FIRST_PAGE = False
                    break
                else:
                    first_row = False
        except:
                pass
        if row.has_attr("href"):
            if ("https" in row["href"] and
                    ("seattle" in row["href"] or "/e/" in row["href"]) and
                    row["href"] not in FOUND_LIST and
                    "login" not in row["href"]):
                first_row = False
                print("Found link " + row["href"] + "\n")
                FOUND_LIST.append(row["href"])
    if FIRST_PAGE:
        FIRST_PAGE = False
        find_pages(url, soup)    
        # Go through queue scraping each page found.
def find_pages(url, soup):
    paginator = re.compile(".*paginator.*")
    max_pages = 0
    page = 2
    for row in soup.findAll(attrs={"class": paginator}):
        for anchor in row.findAll('a'):
            if anchor.text.isdigit():
                max_pages = int(anchor.text)
    while page <= max_pages:
        #print("Opening page " + str(page))
        #print() 
        open_url(url[:-1] + str(page))
        page += 1
            
def get_soup(url):
    response = urllib.request.urlopen(url)
    soup = BeautifulSoup(response, "html.parser")
    return soup

def create_json():
    with open('eventBrite_URL_data.json', 'w') as outfile:
        json.dump(FOUND_LIST, outfile)
    #s3.Object('mjleontest', 'browser_event_data.json').put(Body=open('browser_event_data.json', 'rb'))


def main():
    print("Starting browser crawler; " + str(datetime.now()) + "\n")
    global FOUND_LIST
    try:
        with open('eventBrite_URL_data.json') as data:
            FOUND_LIST = json.load(data)
    except:
        pass 
    open_url(EVENT_BRITE)
    create_json()
    print("Closing browser crawler; " + str(datetime.now()) + "\n")
if __name__ == '__main__':   
    main()
    
    