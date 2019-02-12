# -*- coding: utf-8 -*-
"""
Created on 02/11/2019
NSC - AD440 CLOUD PRACTICIUM
@author: Michael Leon

Scraper for EventBrite

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
import asyncio

OUTPUT = {}

def process_data():
    queue = get_url()
    while queue:
        current_url = queue.pop(0)
        print("Scraping page " + current_url)
        print("URL's remaining in queue - " + str(len(queue)))
        try:       
            inner_soup = get_soup(current_url)
            data = scrape_page(inner_soup, current_url)
            if data:
                OUTPUT[current_url] = data
        except Exception as a:
            print("url failed " + str(a))
        print("Scraping finished")
    create_json()

def get_url():
    with open('browser_URL_data.json') as data:
        queue = json.load(data)
    return queue  

def get_soup(url):
    response = urllib.request.urlopen(url)
    soup = BeautifulSoup(response, "html.parser")
    return soup

def create_json():
    print("creating json...")
    with open('browser_event_data.json', 'w') as outfile:
        json.dump(OUTPUT, outfile)
    #s3.Object('mjleontest', 'browser_event_data.json').put(Body=open('browser_event_data.json', 'rb'))
    
def scrape_page(soup, url):
    data = {}
    keywords = ["disability", 
                "handicap", 
                "disabilities", 
                "disabled", 
                "accomodation", 
                "inclusive",
                "disorder",
                "condition",
                "dysfunction",
                "illness",
                "disease",
                "inability",
                "impairment",
                "injured",
                "injury",
                "weakness",
                "disadvantage"]
    key_found = False
    #Check if keyword appears on the page before proceeding with scrape
    for key in keywords:
        if key in soup.find("body").text.lower():
            #print("SUCCESS found - " + key)
            #print()
            key_found = True
            break
    #Extracts all relevent data to be inserted into the output list.
    if key_found:
        event_re = re.compile('.*event.*')
        price_re = re.compile('.*price.*')
        title_re = re.compile('.*title.*')
        body_re = re.compile('.*body.*')
        date_re = re.compile('.*date.*')
        data["URL"] = url
        if soup.find(text='Location'):
            count = 0
            location = ""
            for row in soup.find(text='Location').find_all_next("p"):
                if count != 3:
                    if len(row.text) <= 64 and not row.find("a"):
                        location += location + row.text + " "
                        #print(row.text)
                elif count >= 3:
                    break    
                count += 1
            data["Location"] = location
        time = ""
        for row in soup.findAll(attrs={"class": title_re}):
            #print(row.text)
            data["Title"] = row.text
            break
        count = 0
        for row in soup.findAll(attrs={"class": date_re}):
            if "am" in row.text.lower() or "pm" in row.text.lower():
                    time += time + row.text
                    data["Time"] = time
            try:
                data["Date"] = str(parse(row.text).date())
            except:
                pass    
        description = ""
        for row in soup.findAll("p"):
            if(len(row.text) >= 100):
                description += description + row.text + " "
                count += 1
                if count == 2:
                    data["Description"] = description
                    break
        if len(data) > 1:
            return data
        else:
            print("Data empty, skipping")
            return False
        if soup.find(attrs={"class": "js-display-price"}):
            data["Price"] = soup.find(attrs={"class": "js-display-price"})
        else:
            data["Price"] = "Unknown"
    else:
        print("Key not found, skipping")

def main():
    process_data()

if __name__ == '__main__':   
    main()