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

# This script scrapes a website and pulls specific data.
FOUND_LIST = []
QUEUE = []
OUTPUT = {}
SOUP = []
EVENT_BRITE = "https://www.eventbrite.com/d/wa--seattle/disability/?page=1"
OFA = "https://outdoorsforall.org/events-news/calendar/"
DESTINATION = [OFA, EVENT_BRITE]

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
                    print("Unique link added to queue - " + row["href"] + "\n")
                    FOUND_LIST.append(row["href"])
                    QUEUE.append(row["href"])
    paginator = re.compile(".*paginator.*")
    max_pages = 0
    page = 1
    # Finds max page number so all events are found
    while QUEUE:
        current_url = QUEUE.pop(0)
        print("Crawling - " + current_url)
        print(str(len(QUEUE)) + " URL's remaining")
        try:       
            if "page=" not in current_url:
                print(current_url)
                OUTPUT[current_url] = scrape_page(soup)
                print("Scraped")
            else:
                print("Finding links...")
                if current_url not in FOUND_LIST:
                    for row in soup.findAll(attrs={"class": paginator}):
                        for anchor in row.findAll('a'):
                            if anchor.text.isdigit():
                                max_pages = int(anchor.text)
                    while page <= max_pages:
                        if page != 1:
                            FOUND_LIST.append(url[:-1] + str(page))
                            QUEUE.append(url[:-1] + str(page))
                        page += 1
            open_url(current_url)
        except Exception as a:
            try:
                print(a)
                print("Rewriting to : " + url + current_url)
                open_url(url + current_url)
            except:
                print("URL failed")
    


def scrape_page(soup):
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
            print("SUCCESS found - " + key)
            key_found = True
            break
    if key_found:
        event_re = re.compile('.*event.*')
        price_re = re.compile('.*price.*')
        title_re = re.compile('.*title.*')
        body_re = re.compile('.*body.*')
        date_re = re.compile('.*date.*')

        if soup.find(text='Location'):
            count = 0
            location = ""
            for row in soup.find(text='Location').find_all_next("p"):
                if count != 3:
                    if len(row.text) <= 64 and not row.find("a"):
                        location += location + row.text + " "
                        print(row.text)
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
            try:
                data["Date"] = str(parse(row.text).date())
            except:
                pass
        data["Time"] = time
        description = ""
        for row in soup.findAll("p"):
            if(len(row.text) >= 100):
                description += description + row.text + " "
                count += 1
                if count == 2:
                    data["Description"] = description
                    break
        return data
    else:
        print("Key not found, skipping")


def create_json():
    print("creating json...")
    with open('browser_event_data.json', 'w') as outfile:
        json.dump(OUTPUT, outfile)

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
            OUTPUT[current_url] = OFAScraper.open_link(current_soup)
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
    
    