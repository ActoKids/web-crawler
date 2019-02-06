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
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import selenium.webdriver.chrome.service as service
from bs4 import BeautifulSoup
import time
from dateutil.parser import parse
from datetime import datetime
from . import OFAScraper
import boto3


# This script scrapes a website and pulls specific data.
FOUND_LIST = []
QUEUE = []
OUTPUT = {}
SOUP = []
EVENT_BRITE = "https://www.eventbrite.com/d/wa--seattle/disability/?page=1"
OFA = "https://outdoorsforall.org/events-news/calendar/"
DESTINATION = [OFA, EVENT_BRITE]
#DESTINATION = [EVENT_BRITE]
#s3 = boto3.resource('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

def open_url(url):
    # Function opens a url, parses it with Beautifulsoup
    # Finds relevant links and adds them to the global QUEUE
    # Foundlist used to avoid duplicates
    global QUEUE
    global DESTINATION

    response = urllib.request.urlopen(url)
    soup = BeautifulSoup(response, "html.parser")
    for row in soup.findAll("a"):
        if row.has_attr("href"):
            if row["href"] not in FOUND_LIST :
                if (("seattle" in row["href"] or 
                    "page=" in row["href"] or "/e/" in row["href"]) and
                     row["href"] not in FOUND_LIST):
                    #print("Link added to queue - " + row["href"] + "\n")
                    FOUND_LIST.append(row["href"])
                    QUEUE.append(row["href"])
    print("Looking for more pages")                
    try:
        #print()
        find_pages(url, soup)
    except:
        print("No more pages found")
        print()
    while QUEUE:
        current_url = QUEUE.pop(0)
        print("Scraping for a new event...")
        print("Links remaining - " + str(len(QUEUE)))
        try:       
            if "login" not in current_url and "page=" not in current_url:
                #print(current_url)
                inner_soup = get_soup(current_url)
                data = scrape_page(inner_soup, current_url)
                if data:
                    OUTPUT[current_url] = data
        except Exception as a:
            print("url failed " + str(a))
        print("Scraping reached end of page")
        print()

def find_pages(url, soup):
    paginator = re.compile(".*paginator.*")
    max_pages = 0
    page = 1
    if url not in FOUND_LIST:
        for row in soup.findAll(attrs={"class": paginator}):
            for anchor in row.findAll('a'):
                if anchor.text.isdigit():
                    max_pages = int(anchor.text)
        while page <= max_pages:
            if page != 1:
                FOUND_LIST.append(url[:-1] + str(page))
                #print("Opening page " + str(page))
                #print()
                open_url(url[:-1] + str(page))
            page += 1
            print("Additional page found!")
    else:
        #print("Unable to find additional pages")
        print()

def get_soup(url):
    response = urllib.request.urlopen(url)
    soup = BeautifulSoup(response, "html.parser")
    return soup

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
    for key in keywords:
        if key in soup.find("body").text.lower():
            #print("SUCCESS found - " + key)
            #print()
            key_found = True
            break
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
        # Extracts all relevant data from page
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
    else:
        print("Key not found, skipping")


def create_json():
    print("creating json...")
    with open('browser_event_data.json', 'w') as outfile:
        json.dump(OUTPUT, outfile)
    #s3.Object('mjleontest', 'browser_event_data.json').put(Body=open('browser_event_data.json', 'rb'))

def ofa_crawl(url):
    print(url)
    global QUEUE
    global FOUND_LIST
    global SOUP
    jsQueue = []
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument("--log-level=3")
    driver = webdriver.Chrome(chrome_options=options)
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    pages = 3
    while pages <= 3:
        for row in soup.find_all("div"):
            if row.get("onclick"):
                jsQueue.append(row.get("class")[0])
        #driver.find_element_by_xpath("//*[@id='main_cal']/tbody/tr/td/table/tbody/tr[1]/td[3]/a").click()
        pages += 1
        x = driver.find_elements_by_class_name(jsQueue[0])
    count = 0
    for row in x:
        row.click()
        driver.switch_to.window(driver.window_handles[1])
        if driver.current_url not in FOUND_LIST:
            print()
            print("Scraping for a new event...")
            #QUEUE.append(driver.current_url)
            FOUND_LIST.append(driver.current_url)
            print("Links remaining - " + str(len(jsQueue)))
            jsQueue.pop(0)
            current_url = driver.current_url
            current_soup = BeautifulSoup(driver.page_source, "html.parser")
            for linebreak in current_soup.find_all('br'):
                linebreak.extract()
            OUTPUT[current_url] = OFAScraper.open_link(current_soup, current_url)
            #SOUP.append(BeautifulSoup(driver.page_source, "html.parser"))
            driver.switch_to.window(driver.window_handles[0])
            print("Scraping reached end of page")
        else:
            driver.switch_to.window(driver.window_handles[0])
        #count += 1
        if count == 3:
            break
    driver.quit()

def main():
    start_time = time.time()
    print("Crawler Started.")
    count = 0
    for url in DESTINATION:
        if url == OFA:
            while count != 5:
                try:
                    print("OFA Crawl Started.")
                    #open_url(EVENT_BRITE)
                    for url in DESTINATION:
                        ofa_crawl(url)
                        print("OFA Crawl Completed.")
                        break
                    break
                except Exception as e:
                    print("Error gathering URL data, " + str(e))
                    if str(e) == "list index out of range":
                        count += 1
                        print("Retrying selenium...")
                    else:
                        break
        else:
            print("Typical Crawl Started.")
            open_url(url)
            print("Typical Crawl Completed.")
    create_json()
    elapsed_time = time.time() - start_time
    print("Crawler Ended.")
    print(elapsed_time)
    
if __name__ == '__main__':   
    main()
    
    