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

FOUND_LIST = []
OUTPUT = {}
SOUP = []

def open_link(current_soup, current_url):
    OUTPUT["URL"] = current_url
    find_title(current_soup)
    find_date(current_soup)  
    return OUTPUT   

def find_title(soup):
    global OUTPUT
    
    if soup.find(class_="header-theme"):
        title = soup.find(class_="header-theme").text
        OUTPUT["Title"] = title
        find_description(soup)

def find_description(soup):
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
        OUTPUT["Time"] = time
    else:
        OUTPUT["Time"] = "Unknown"
    for row in desc.findAll(text=True, recursive=False):
        if(len(row) > 1):
            loc = re.sub("\r\n", "", row)
            find_location(loc)
            break
    OUTPUT["Description"] = lol

def find_date(soup):
    global OUTPUT
    header_re = re.compile('.*header.*')
    for row in soup.findAll(attrs={"class": header_re}):
        try:
            for val in row:
                if parse(val):
                    OUTPUT["Date"] = str(parse(val))
                    break
        except Exception as a:
            #print(a)
            pass
        try:
            if "pm" in str(row.lower()) or "am" in str(row.lower()):
                print("Time found!")
        except:
            pass

def find_location(location):
    global OUTPUT
    OUTPUT["Location"] = location
    #print(OUTPUT)W
