# -*- coding: utf-8 -*-
"""
Created on 01/20/2019
NSC - AD440 CLOUD PRACTICIUM
@authors: Nicholas Bennett, Dao Nguyen, Ryan Berry, Kyrrah Nork, Michael Leon

"""
from fbEventCrawler import fbEventCrawler
from browserCrawler import browserCrawler
from browserCrawler import OFAScraper
from googleCalendarCrawler import calendarCrawler   

def main ():
    try:
        fbEventCrawler.main()
    except:
        print("Facebook Crawler failed, check ACCESS_TOKEN")
    try:
        calendarCrawler.main()
    except:
        print("Google Calendar Crawler Failed")
    try:
        browserCrawler.main()
    except Exception as a:
        print("Browser Crawler failed, please review. " + str(a))

main()