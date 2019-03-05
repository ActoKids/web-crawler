# -*- coding: utf-8 -*-
"""
Created on 02/17/2019
NSC - AD440 CLOUD PRACTICIUM
@author: Dao Nguyen

Changed ownership on 03/01/2019
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
import bs4 as bs
import time
from dateutil.parser import parse
from datetime import datetime
import datetime as dt
import boto3
import uuid

dynamodb = boto3.resource('dynamodb', 'us-east-1')
f = open("sslog.log", "w")
OUTPUT = []
ADDRESS = ['Renton: Lindbergh HS Pool: 16740 128th Ave SE Renton, WA 98058',
           'Shoreline Pool: 19030 1st Ave NE Shoreline, WA 98155',
           'Juanita Aquatic Center: 01 NE 132nd St Kirkland, WA 98034 425-936-1627',
           'Hazen High School: 1101 Hoquiam Ave NE Renton, WA 98059 425-204-4230']
#This script scrapes a website and pulls specific data.
def main():
    print("Starting SS Scraper; " + str(datetime.now()), file=f)
    try:
        print("Connecting to http://www.shadowsealsswimming.org/Calendar.html; success", file=f)
        source = urllib.request.urlopen('http://www.shadowsealsswimming.org/Calendar.html').read()
        soup = bs.BeautifulSoup(source,'html.parser')

        table = soup.table
        table = soup.find('table')
        table_rows = table.find_all('tr')
        for tr in table_rows:
            td = tr.find_all('td')
            row = [i.text for i in td]
            data = {}
            
            find_date = row[0].replace(' - ', '-')
            find_date = find_date.replace(',', '').split(' ')
            find_location = row[2].split(' ')

            target_title = ""
            for find_title in find_location:
                if find_title != "-":
                    target_title = target_title + find_title + " "
                else:
                    break
            data["Title"] = target_title.strip('\xa0').strip('\n')

            if len(find_date) >= 3:
                date_string = find_date[0] + ' ' + find_date[1] + ' ' + find_date[2].strip('\n')
                if '-' in find_date[1]:
                    date_operation = find_date[1].split('-')
                    
                    for x in range(int(date_operation[0]), int(date_operation[1]) + 1):
                        new_date_string = ""
                        new_date_string = new_date_string + find_date[0] + ' ' + \
                            str(x) + ' ' + find_date[2].strip('\n')

                        date_object = validate_date(new_date_string)
                        if date_object:
                            data["Date"] = date_object.strftime(
                                '%Y-%m-%d')
                        for i in td:
                            time = ""
                            event_des = ""
                            if ("pm" in row[1].lower() or "am" in row[1].lower()) and any(c.isdigit() for c in row[1]):
                                time += row[1]
                                data["Time"] = time.replace('\n', '')
                            
                        
                            for location in find_location:
                                for address in ADDRESS:
                                    if location in address:
                                        data["Location"] = address
                            data["Desription"] = row[2].replace('\n', '').replace('\xa0', '')
                        #print(data)
                        OUTPUT.append(data)

                else:
                    date_object = validate_date(date_string)
                    if date_object:
                        data["Date"] = date_object.strftime(
                            '%Y-%m-%d')
                    else: 
                        data["Date"] = row[0].strip('\xa0')

                    for i in td:
                        time = ""
                        event_des = ""
                        if ("pm" in row[1].lower() or "am" in row[1].lower()) and any(c.isdigit() for c in row[1]):
                            time += row[1]
                            data["Time"] = time.replace('\n','')
                    

                        
                        for location in find_location:
                            for address in ADDRESS:
                                if location in address:
                                    data["Location"] = address
                        data["Description"] = row[2].replace('\n', '').replace('\xa0', '')
                #print(row)
                    if "Location" not in data:
                        data["Location"] = "Unknown"
                    if "Time" not in data:
                        data["Time"] = "Unknown"
                    data["URL"] = "http://www.shadowsealsswimming.org/Calendar.html"
                    data["ID"] = str(uuid.uuid3(uuid.NAMESPACE_DNS, data["Title"] + data["Date"]))
                    print("Found event " + data["Title"], file=f)
                    to_dynamo(data) 
    except:
        print("Connecting to http://www.shadowsealsswimming.org/Calendar.html; failed", file=f)
    print("Ending SS Scraper; " + str(datetime.now()), file=f)     

def to_dynamo(data):
    table = dynamodb.Table('events')
    table.put_item(Item={'ID': data['ID'],
                        'URL': data['URL'],
                        'Title': data['Title'],
                        'Description': data['Description'],
                        'Location': data['Location'],
                        'Date': data['Date']})   
    #s3.Object('mjleontest', 'browser_event_data.json').put(Body=open('browser_event_data.json', 'rb'))

# This function to check the date in string and return if date is valid or not
def validate_date(date_text):
    date_string = date_text
    new_date_string = ""
    fmts = ('%Y','%b %d, %Y','%b %d, %Y','%B %d, %Y','%B %d %Y','%m/%d/%Y','%m/%d/%y','%b %Y','%B%Y','%b %d,%Y', '%b %d %Y')
    month = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')
    
    date_string = date_string.split(' ')
    for find_month in month:
        if find_month in date_string[0]:
            set_month = find_month
            new_date_string += set_month + ' ' + date_string[1] + ' ' + date_string[2]

    for fmt in fmts:
        try:
            t = dt.datetime.strptime(new_date_string, fmt)
                #print(t)
            return t
            break
        except ValueError as err:
            pass

if __name__ == '__main__':
    main()
