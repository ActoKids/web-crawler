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


# This script scrapes a website and pulls specific data.
FOUND_LIST = []
QUEUE = []
OUTPUT = {}
SOUP = []
SHADOWSEALS = {"Shoreline Pool":"19030 1st Ave NE, Shoreline, WA 98155",
                "Lindbergh HS Pool, Renton":"16740 128th Ave SE, Renton, WA 98058",
                "Hazen HS Pool":"1101 Hoquiam Ave NE, Renton, WA 98059",
                "Juanita Aquatic Center":"10601 NE 132nd St Kirkland, WA 98034"}
EVENT_BRITE = "https://www.eventbrite.com/d/wa--seattle/disability/?page=1"
OFA = "https://outdoorsforall.org/events-news/calendar/"
DESTINATION = [OFA]

def open_url(url):
    # Function opens a url, parses it with Beautifulsoup
    # Finds relevant links and adds them to the global QUEUE
    # Foundlist used to avoid duplicates
    global QUEUE
    body = re.compile(".*body.*")
    response = urllib.request.urlopen(url)
    soup = BeautifulSoup(response, "html.parser")
    scan_page(soup)
    soup = soup.find(attrs={"class": body})

    for row in soup.findAll("a"):
        if row.has_attr("href"):
            if row["href"] not in FOUND_LIST and "eventbrite" in row["href"]:
                if ("seattle" in row["href"] or "/e/" in row["href"] and row["href"] not in FOUND_LIST):
                    print("Unique link added to queue - " + row["href"] + "\n")
                    FOUND_LIST.append(row["href"])
                    QUEUE.append(row["href"])
    paginator = re.compile(".*paginator.*")
    max_pages = 0
    page = 1
    # Finds max page number so all events are found
    if url not in FOUND_LIST:
        for row in soup.findAll(attrs={"class": paginator}):
            for anchor in row.findAll('a'):
                if anchor.text.isdigit():
                    max_pages = int(anchor.text)
        while page <= max_pages:
            if page != 1:
                FOUND_LIST.append(url[:-1] + str(page))
                QUEUE.append(url[:-1] + str(page))
            page += 1
    while QUEUE:
        current_url = QUEUE.pop(0)
        print("Opening - " + current_url)
        print(str(len(QUEUE)) + " URL's remaining")
        try:
            #print("\nOpening found link - " + current_url)
            open_url(current_url)
        except Exception as a:
            try:
                print(a)
                open_url(url + current_url)
            except:
                print("URL failed")
    


def scan_page(soup):
    global OUTPUT
    event_re = re.compile('.*event.*')
    price_re = re.compile('.*price.*')
    event_data = {"Title": None, "Date": None,
                  "Location": None, "Description": None, "Price": None}
    # Extracts all relevant data from page
    for row in soup.findAll("div", attrs={"class": event_re}):
        for data in row.findAll('h3'):
            if data.text != " " and data.find_next('p'):
                if("date" in data.text.lower() or "location" in data.text.lower() or
                        "description" in data.text.lower()):
                    if "date" in data.text.lower():
                        event_data["Date"] = data.find_next('p').text
                    if "location" in data.text.lower():
                        location = " "
                        for tag in data.find_next('div').findAll("p"):
                            if not tag.find("a"):
                                location = location + tag.text + " "
                            event_data["Location"] = location
                        else:
                            break
                    if "description" in data.text.lower():
                        event_data["Description"] = data.find_next(
                            'p').text.replace('\n', " ")
        for title in row.findAll('h1'):
            if title.text != " " and event_data["Title"] is None:
                event_data["Title"] = title.text
    for price in soup.findAll(attrs={"class": price_re}):
        event_data["Price"] = price.text.strip()
    # Data is useless if Title, Date, and Location is missing. Catch duplicates.
    if (event_data["Title"] is not None and event_data["Location"] is not None and
            event_data["Date"] is not None and event_data["Title"] not in OUTPUT):
        if event_data["Description"] is None or event_data["Description"] == "":
            event_data["Description"] = "None"
        if event_data["Price"] is None or event_data["Price"] == "":
            event_data["Price"] = "Unknown"
        print("Event found! - " + event_data["Title"] +"\n")
        OUTPUT[event_data["Title"]] = event_data
    else:
        print("Data missing, ignoring URL" + "\n")


def create_json():
    with open('browser_event_data.json', 'w') as outfile:
        json.dump(OUTPUT, outfile)

def find_url_selenium(url):
    #print(url)
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
    for row in soup.find_all("div"):
        if row.get("onclick"):
            jsQueue.append(row.get("class")[0])
    x = driver.find_elements_by_class_name(jsQueue[0])
    count = 0
    for row in x:
        row.click()
        driver.switch_to.window(driver.window_handles[1])
        if driver.current_url not in FOUND_LIST:
            print()
            print("Scraping for a new event...")
            QUEUE.append(driver.current_url)
            FOUND_LIST.append(driver.current_url)
            print("Links remaining - " + str(len(jsQueue) - len(QUEUE)))
            current_url = driver.current_url
            current_soup = BeautifulSoup(driver.page_source, "html.parser")
            for linebreak in current_soup.find_all('br'):
                linebreak.extract()
            open_link(current_soup, current_url)
            #SOUP.append(BeautifulSoup(driver.page_source, "html.parser"))
            driver.switch_to.window(driver.window_handles[0])
            print("Scraping reached end of page")
        else:
            driver.switch_to.window(driver.window_handles[0])
        #count += 1
        if count == 3:
            break
    driver.quit()

def open_link(current_soup, current_url):
    find_title(current_soup, current_url)
    find_date(current_soup, current_url)       

def find_title(soup, current_url):
    global OUTPUT
    
    if soup.find(class_="header-theme"):
        title = soup.find(class_="header-theme").text
        #print(title)
        OUTPUT[current_url] = {"Title" : title}
        find_description(soup, current_url)
        #find_date(soup, title)
        #find_location(soup,title)
        #print(OUTPUT)

def find_description(soup, current_url):
    global OUTPUT
    desc = soup.find("span", attrs={"class": "event-desc-theme"})
    #print(desc)
    lol = ""
    loc = ""
    time = ""
    for row in desc.findAll("p"):
        try:
            if "Export:" not in row.text:
                if "location" in row.text.lower():
                   pass
                else:
                    lol = lol + row.text
                if ("pm" in row.text.lower() or "am" in row.text.lower()) and any(c.isdigit() for c in row.text):
                    #print(row.text)
                    time += row.text + " "
                #print(row.text)
        except:
            pass
    if time != "":
        OUTPUT[current_url].update({"Time" : time})
    else:
        OUTPUT[current_url].update({"Time" : "Unknown"})
    for row in desc.findAll(text=True, recursive=False):
        if(len(row) > 1):
            loc = re.sub("\r\n", "", row)
            find_location(loc, current_url)
            break
    OUTPUT[current_url].update({"Description" : lol})

def find_date(soup, current_url):
    global OUTPUT
    header_re = re.compile('.*header.*')
    #print(soup.findAll(attrs={"class": header_re}))
    #print(len(soup.findAll(attrs={"class": header_re})))
    for row in soup.findAll(attrs={"class": header_re}):
        try:
            for val in row:
                if parse(val):
                    OUTPUT[current_url].update({"Date" : str(parse(val))})
                    break
        except Exception as a:
            #print(a)
            pass
        try:
            if "pm" in str(row.lower()) or "am" in str(row.lower()):
                print("Time found!")
        except:
            pass

def find_location(location, current_url):
    global OUTPUT
    OUTPUT[current_url].update({"Location" : location})
    #print(OUTPUT)W

def main():
    count = 0
    while count != 5:
        try:
            print("Browser Events Crawl Started.")
            #open_url(EVENT_BRITE)
            for url in DESTINATION:
                find_url_selenium(url)
                print("Browser Events Crawl Completed.")
                create_json()
                break
            break
        except Exception as e:
            print("Error gathering URL data, " + str(e))
            if str(e) == "list index out of range":
                count += 1
                print("Retrying selenium...")
            else:
                break
    
if __name__ == '__main__':
    start_time = time.time()
    main()
    elapsed_time = time.time() - start_time
    print(elapsed_time)