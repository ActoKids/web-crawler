from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

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
import uuid
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import selenium.webdriver.chrome.service as service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
from dateutil import parser
from datetime import datetime
import boto3
# This script scrapes a website and pulls specific data.
FOUND_LIST = []
QUEUE = []
OUTPUT = {}
DATA = {}
SOUP = []
OFA = "https://outdoorsforall.org/events-news/calendar/"

dynamodb = boto3.resource('dynamodb', 'us-east-1')


def ofa_crawl(url):
    global QUEUE
    global FOUND_LIST
    global SOUP
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1280x1696')
    chrome_options.add_argument('--user-data-dir=/tmp/user-data')
    chrome_options.add_argument('--hide-scrollbars')
    chrome_options.add_argument('--enable-logging')
    chrome_options.add_argument('--log-level=0')
    chrome_options.add_argument('--v=99')
    chrome_options.add_argument('--single-process')
    chrome_options.add_argument('--data-path=/tmp/data-path')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--homedir=/tmp')
    chrome_options.add_argument('--disk-cache-dir=/tmp/cache-dir')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')
    chrome_options.binary_location = os.getcwd() + "/bin/headless-chromium"

    driver = webdriver.Chrome(chrome_options=chrome_options)
    pages = 1

    # Grab all links on calendar for 3 months from current month
    print("Starting OFA Crawler; " + str(datetime.now()))

    while pages <= 3:
        jsQueue = []
        if pages == 1:
            try:
                driver.get(url)
                print("\nConnecting to " + url + "; success\n") 
            except:
                print("\nConnecting to " + url + "; failed\n")  
            
        # set selenium to click to the next month from current calendar month
        if pages == 2:  
            driver.get(url)
            WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.XPATH, "//a[img[@alt='Forward']]"))).click()    
        # set selenium to click to the month after next month
        elif pages == 3:
            driver.get(url)
            WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.XPATH, "//a[img[@alt='Forward']]"))).click()
            time.sleep(1)
            driver.find_element_by_xpath("//a[img[@alt='Forward']]").click()
            
        # parse the pages and add all links found to a list
        soup = BeautifulSoup(driver.page_source, "html.parser")  
        for row in soup.find_all("div"):
            if row.get("onclick"):
                jsQueue.append(row.get("class")[0])
        try:
            x = driver.find_elements_by_class_name(jsQueue[0])
        except:
            pass

        # to refresh the elements and retrieve them on the current page
        if pages >= 2 :  
            time.sleep(0.45)  
            count = 0   
            while count != 5:
                soup = BeautifulSoup(driver.page_source, "html.parser")  
                for row in soup.find_all("div"):
                    if row.get("onclick"):
                        jsQueue.append(row.get("class")[0])
                try:
                    x = driver.find_elements_by_class_name(jsQueue[0])
                except:
                    pass
                count += 1
                      
        # Click all found elements to open page and grab the URL
        for row in x:
            row.click()
            driver.switch_to.window(driver.window_handles[1])

            # check for links that previously found from the previous month, if not found 
            # add to list
            if driver.current_url not in FOUND_LIST:
 
                FOUND_LIST.append(driver.current_url)
                
                current_url = driver.current_url
                current_soup = BeautifulSoup(driver.page_source, "html.parser")
                for linebreak in current_soup.find_all('br'):
                    linebreak.extract()
                # Calls OFAScraper module to populate a dictionary object to add to the output
                data = open_link(current_soup, current_url)
                table = dynamodb.Table('events')
                try:
                    table.put_item(Item={"event_id": data["event_id"],
                                        "event_link": data["event_link"],
                                        "event_name": data["event_name"],
                                        "description": data["description"],
                                        "location_address": data["location_address"],
                                        "start_date_time": data["start_date_time"],
                                        "user_name": data["user_name"],
                                        "activity_type": data["activity_type"],
                                        "org_name": data["org_name"],
                                        "location_name": data["location_name"],
                                        "contact_name": data["contact_name"],
                                        "contact_phone": data["contact_phone"],
                                        "contact_email": data["contact_email"],
                                        "end_date_time": data["end_date_time"],
                                        "frequency": data["frequency"],
                                        "cost": data["cost"],
                                        "picture_url": data["picture_url"],
                                        "min_age": data["min_age"],
                                        "max_age": data["max_age"],
                                        "disability_types": data["disability_types"],
                                        "inclusive_event": data["inclusive_event"],
                                        "event_status": data["event_status"],
                                        "approver": data["approver"],
                                        "created_timestamp": data["created_timestamp"]},
                                    ConditionExpression = "attribute_not_exists(event_id)")
                    print("Found event " + data["event_name"])
                except Exception as A:
                    print("Event "+ data["event_name"] +" exists already.")
                driver.switch_to.window(driver.window_handles[0])

            else:
                driver.switch_to.window(driver.window_handles[0])

        pages += 1
    driver.quit()

# This open work on the data from each link, call for helpers to get additional data
# return data and status
def open_link(current_soup, current_url):
    data = {}    
    data["event_id"] = str(uuid.uuid5(uuid.NAMESPACE_DNS, current_url))
    data["event_link"] = current_url
    data["event_name"] = str(find_title(current_soup))
    data["description"] = str(find_description(current_soup))
    data["location_address"] = str(find_location(current_soup))
    data["start_date_time"] = str(find_date(current_soup))
    data["user_name"] = "None"
    data["activity_type"] = "Contact organizer for details"
    data["org_name"] = "Outdoor's for All"
    data["location_name"] = "Contact organizer for details"
    data["contact_name"] = "Contact organizer for details"
    data["contact_phone"] = "Contact organizer for details"
    data["contact_email"] = "Contact organizer for details"
    data["end_date_time"] = "Contact organizer for details"
    data["frequency"] = "Contact organizer for details"
    data["cost"] = "Contact organizer for details"
    data["picture_url"] = "<img src=\"https://pbs.twimg.com/profile_images/950894553162117121/Q88YRLQ8_400x400.jpg\">"
    data["min_age"] = "Contact organizer for details"
    data["max_age"] = "Contact organizer for details"
    data["disability_types"] = "Contact organizer for details"
    data["inclusive_event"] = "Contact organizer for details"
    data["event_status"] = "pending"
    data["approver"] = "N/A"
    data["created_timestamp"] = str(datetime.now())

    return data

# This function to get the title of each event from link
def find_title(soup):
    if soup.find(class_="header-theme"):
        title = soup.find(class_="header-theme").text
        title = title.replace('\n', '')
        title = title.replace('\t', '')
        return title
        

# This function to get the description of each event from link
def find_description(soup):
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
                    url = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+] |[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', row.text)
                    if url:
                        for word in row.text.split():
                            if 'http' in word:
                                link_url = '<a href="{}"'.format(word) + ' target="{}"><strong>'.format('_blank') + word + '</strong></a>'
                                p_desc = p_desc + link_url + " "
                            else:
                                p_desc = p_desc + word + " "
                           
                    else: 
                        p_desc = p_desc + row.text                             
                        if row.findAll("a"):
                            for link in row.findAll("a"):
                                if link.has_attr('href'):
                                    link_url = '<a href="{}"'.format(link['href']) + ' target="{}"><strong>'.format('_blank') + link.text + '</strong></a>'
                                    if link.text in p_desc:
                                        p_desc = p_desc.replace(link.text, link_url)
                                        
                if ("pm" in row.text.lower() or "am" in row.text.lower()) and any(c.isdigit() for c in row.text):
                    time += row.text + " "
        except:
            pass
    if not p_desc:
        p_desc = "None"
    return(p_desc)

#This function to get the date from each event from link
def find_date(soup):
    date = ""
    for row in soup.findAll(attrs={"class": "subheader-theme"}):
        row = row.text.splitlines()
        try:
            time = ""
            for val in row:
                if "-" in val:
                    val = val.split("-")
                    time = val[0]
                else:
                    if time == "":
                        try:
                            date = str(parser.parse(val))
                        except:
                            pass
                    else:
                        try:
                            date = str(parser.parse(val +" "+ time))
                            time = ""
                        except Exception as A:
                            #print(A)
                            pass
        except:
            pass
    if date == "":
        return("Unknown")
    else:
        return date

# This function to get the location of each event from link
def find_location(soup):
    desc = soup.find("span", attrs={"class": "event-desc-theme"})
    loc = ""
    for row in desc.findAll(text=True, recursive=False):
        if(len(row) > 1):
            loc = re.sub("\r\n", "", row)
    if len(loc) > 0:
        return(loc.replace('\n', '').replace('\t', ''))
    else:
        return("Unknown")
    # print(OUTPUT)W

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
    print("\nClosing OFA Crawler; " + str(datetime.now()))


if __name__ == '__main__':
    main()

def lambda_handler(event, context):
    global FOUND_LIST
    FOUND_LIST = []
    main()
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }