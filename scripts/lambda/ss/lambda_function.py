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
from bs4 import BeautifulSoup
import bs4 as bs
import time as timeparse
from dateutil import parser
from datetime import datetime
import datetime as dt
import boto3
import uuid

dynamodb = boto3.resource('dynamodb', 'us-east-1')
#f = open("sslog.log", "w")
OUTPUT = []
ADDRESS = ['Renton: Lindbergh HS Pool: 16740 128th Ave SE Renton, WA 98058',
           'Shoreline Pool: 19030 1st Ave NE Shoreline, WA 98155',
           'Juanita Aquatic Center: 01 NE 132nd St Kirkland, WA 98034 425-936-1627',
           'Hazen High School: 1101 Hoquiam Ave NE Renton, WA 98059 425-204-4230']
#This script scrapes a website and pulls specific data.
def main():
    #print("Starting SS Scraper; " + str(datetime.now()), file=f)
    print("Starting SS Scraper; " + str(datetime.now()))
    try:
        #print("Connecting to http://www.shadowsealsswimming.org/Calendar.html; success", file=f)
        print("Connecting to http://www.shadowsealsswimming.org/Calendar.html; success")
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
            data["event_name"] = target_title.strip('\xa0').strip('\n')

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
                            data["start_date_time"] = date_object.strftime(
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
                                        data["location_address"] = address
                            data["description"] = row[2].replace('\n', '').replace('\xa0', '')
                        #print(data)
                        OUTPUT.append(data)

                else:
                    date_object = validate_date(date_string)
                    if date_object:
                        data["start_date_time"] = date_object.strftime(
                            '%Y-%m-%d')
                    else: 
                        data["start_date_time"] = row[0].strip('\xa0')

                    for i in td:
                        time = ""
                        event_des = ""
                        if ("pm" in row[1].lower() or "am" in row[1].lower()) and any(c.isdigit() for c in row[1]):
                            time = row[1]
                            time = time.split("-")
                            try:
                                time = time[0]+" pm"
                                data["start_date_time"] = data["start_date_time"]+" "+(timeparse.strftime("%H:%M:%S", timeparse.strptime(time, "%I:%M %p")))
                                break
                            except Exception as A:
                                print(A)

                        
                    for location in find_location:
                        for address in ADDRESS:
                            if location in address:
                                data["location_address"] = address
                    data["description"] = row[2].replace('\n', '').replace('\xa0', '')
                #print(row)
                    if "Location" not in data:
                        data["location_address"] = "Unknown"
                    if "Time" not in data:
                        data["Time"] = "Unknown"
                    data["event_link"] = "http://www.shadowsealsswimming.org/Calendar.html"
                    data["event_id"] = str(uuid.uuid5(uuid.NAMESPACE_DNS, data["event_name"] + data["start_date_time"]))
                    #print("Found event " + data["Title"], file=f)
                    data["user_name"] = "None"
                    data["activity_type"] = "Contact organizer for details"
                    data["org_name"] = "Shadow Seals Swimming"
                    data["location_name"] = "Contact organizer for details"
                    data["contact_name"] = "Contact organizer for details"
                    data["contact_phone"] = "Contact organizer for details"
                    data["contact_email"] = "Contact organizer for details"
                    data["end_date_time"] = "Contact organizer for details"
                    data["frequency"] = "Contact organizer for details"
                    data["cost"] = "Contact organizer for details"
                    data["picture_url"] = "<img src=\"http://www.shadowsealsswimming.org/images/c03de8f057c6e9610d95a251f7085d95_944j.png\">"
                    data["min_age"] = "Contact organizer for details"
                    data["max_age"] = "Contact organizer for details"
                    data["disability_types"] = "Contact organizer for details"
                    data["inclusive_event"] = "Contact organizer for details"
                    data["event_status"] = "pending"
                    data["approver"] = "N/A"
                    data["created_timestamp"] = str(datetime.now())
                    to_dynamo(data) 
    except:
        #print("Connecting to http://www.shadowsealsswimming.org/Calendar.html; failed", file=f)
        print("Connecting to http://www.shadowsealsswimming.org/Calendar.html; failed")
    #print("Ending SS Scraper; " + str(datetime.now()), file=f)  
    print("Ending SS Scraper; " + str(datetime.now()))     

def to_dynamo(data):
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
        print("Event " + data["event_name"] + " exists already.")
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
def lambda_handler(event, context):
    main()
    return {
        'statusCode': 200,
        'body': json.dumps('SSScraper ran successfully')
    }
