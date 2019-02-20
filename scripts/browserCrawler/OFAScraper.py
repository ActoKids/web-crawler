# -*- coding: utf-8 -*-
"""
Created on 01/27/2019
NSC - AD440 CLOUD PRACTICIUM
@author: Michael Leon

Changed ownership on 02/09/2019
@author: Dao Nguyen
Last edited by Dao Nguyen 02/19/2019

"""

import urllib.request
import re
import os
import json
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import selenium.webdriver.chrome.service as service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from dateutil.parser import parse
from datetime import datetime
import boto3


# This script scrapes a website and pulls specific data.
FOUND_LIST = []
QUEUE = []
OUTPUT = {}
DATA = {}
SOUP = []
OFA = "https://outdoorsforall.org/events-news/calendar/"
#s3 = boto3.resource('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)


def ofa_crawl(url):
    global QUEUE
    global FOUND_LIST
    global SOUP
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument("--log-level=3")
    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)
    pages = 1
    quece_copy = []

    # Grab all links on calendar for 3 months from current month
    print()
    print("Starting browser scraper; " + str(datetime.now()))

    while pages <= 3:
        jsQueue = []
        driver.get(url)     
            
        # set selenium to click to the next month from current calendar month
        if pages == 2:      
            driver.find_element_by_xpath("//a[img[@alt='Forward']]").click()
             
        # set selenium to click to the month after next month
        elif pages == 3:
            driver.find_element_by_xpath("//a[img[@alt='Forward']]").click()
            time.sleep(2)
            driver.find_element_by_xpath("//a[img[@alt='Forward']]").click()
            

        print()
        print("Scrapping page: " + str(pages) +"...")

        # parse the pages and add all links found to a list
        soup = BeautifulSoup(driver.page_source, "html.parser")  
        for row in soup.find_all("div"):
            if row.get("onclick"):
                jsQueue.append(row.get("class")[0])
    
        x = driver.find_elements_by_class_name(jsQueue[0])

        # to refresh the elements and retrieve them on the current page
        if pages >= 2 :       
            soup = BeautifulSoup(driver.page_source, "html.parser")  
            for row in soup.find_all("div"):
                if row.get("onclick"):
                    jsQueue.append(row.get("class")[0])
            x = driver.find_elements_by_class_name(jsQueue[0])

            soup = BeautifulSoup(driver.page_source, "html.parser")  
            for row in soup.find_all("div"):
                if row.get("onclick"):
                    jsQueue.append(row.get("class")[0])
            x = driver.find_elements_by_class_name(jsQueue[0])
                  
  
        quece_copy = x
        link_count = len(x)
        print(str(link_count) + " Links found")
     
        
        # Click all found elements to open page and grab the URL
        for row in x:
            row.click()
            driver.switch_to.window(driver.window_handles[1])

            # check for links that previously found from the previous month, if not found 
            # add to list
            if driver.current_url not in FOUND_LIST:
 
                FOUND_LIST.append(driver.current_url)
                
                jsQueue.pop(0)
                current_url = driver.current_url
                current_soup = BeautifulSoup(driver.page_source, "html.parser")
                for linebreak in current_soup.find_all('br'):
                    linebreak.extract()
                # Calls OFAScraper module to populate a dictionary object to add to the output
                OUTPUT[current_url] = open_link(current_soup, current_url)
                print(str(link_count - 1) + " remain") 
                driver.switch_to.window(driver.window_handles[0])

            else:
                driver.switch_to.window(driver.window_handles[0])
           
            link_count -=1
        pages += 1
    driver.quit()

# This open work on the data from each link, call for helpers to get additional data
# return data and status
def open_link(current_soup, current_url):
    data = {}
    try:       
        print("Connecting to " + current_url + "; success")
        data["URL"] = current_url
        find_title(current_soup, data)
        find_date(current_soup, data)
        if data:
            print("Scraping finished " + current_url + "; success")
            return data
        else:
            print("Scraping finished " + current_url + "; failed")
    except:
        print("Connecting to " + current_url + "; failed")

# This function to get the title of each event from link
def find_title(soup, data):
    if soup.find(class_="header-theme"):
        title = soup.find(class_="header-theme").text
        title = title.replace('\n', '')
        title = title.replace('\t', '')
        data["Title"] = title
        find_description(soup, data)

# This function to get the description of each event from link
def find_description(soup, data):
    desc = soup.find("span", attrs={"class": "event-desc-theme"})
    p_desc = ""
    loc = ""
    time = ""
    # Look for all p elements to find description, ignore location and attempt to find time.
    for row in desc.findAll("p"):
        try:
            if "Export:" not in row.text:
                if "location" in row.text.lower():
                    pass
                else:
                    p_desc = p_desc + row.text
                if ("pm" in row.text.lower() or "am" in row.text.lower()) and any(c.isdigit() for c in row.text):
                    time += row.text + " "
        except:
            pass
    if time != "":
        data["Time"] = time.replace('\u00a0', '')
    else:
        data["Time"] = "Unknown"
    for row in desc.findAll(text=True, recursive=False):
        if(len(row) > 1):
            loc = re.sub("\r\n", "", row)
            find_location(loc, data)
            break
    data["Description"] = p_desc

#This function to get the date from each event from link
def find_date(soup, data):
    header_re = re.compile('.*header.*')
    for row in soup.findAll(attrs={"class": header_re}):
        try:
            for val in row:
                if parse(val):
                    data["Date"] = str(parse(val))
                    break
        except Exception as a:
            pass
        try:
            if "pm" in str(row.lower()) or "am" in str(row.lower()):
                print("Time found!")
        except:
            pass

# This function to get the location of each event from link
def find_location(location, data):
    data["Location"] = location.replace('\n', '').replace('\t', '')
    # print(OUTPUT)W

# This function to create a json file
def create_json():
    with open('OFA_event_data.json', 'w') as outfile:
        json.dump(OUTPUT, outfile)

# Main function
def main():
    count = 0
    while count != 5:
        try:
            ofa_crawl(OFA)
            break
        except Exception as e:
            print("Error gathering URL data, " + str(e))
            if str(e) == "list index out of range":
                count += 1
                print("Retrying selenium...")
            else:
                break

    create_json()
    print("Closing browser scraper; " + str(datetime.now()))


if __name__ == '__main__':
    main()