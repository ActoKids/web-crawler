# -*- coding: utf-8 -*-
"""
Created on Tues  01/15/2019
NSC - AD440 CLOUD PRACTICIUM
@author: Dao Nguyen

"""

import urllib3
import requests
import facebook
import json

#Facebook API Version, with current facbook Library only support up to v3.1
API_VERSION = '3.1'

#User facebook access token
ACCESS_TOKEN = 'EAAHtVhajj5kBAHG6cXwVCJpoZA0q4dpsZAT59XPBJ4S93Ad6JZCrqqZBNnW2\
                ZBuXSgbUEDZALddlbyfaMY91szP3X2EwF3jMK2MFBguDU2ANowmEu8PeOgWgyt\
                dMy4zhlvFERZA0RshPFEWuUFM2ZCvQgCmCWMP3zKRWHZAcBAY9oGIjW0PXtNKhW'

#All current fields from a facebook event right now. Facebook might add more fields 
#or remove these fields in the future. Always check https://developers.facebook.com/docs/graph-api/reference/event/
#for current facebook event fields.
EVENT_FIELDS = ['attending_count',
                'can_guests_invite',
                'category',
                'cover',
                'declined_count',
                'description',
                'discount_code_enabled',
                'end_time,event_times',
                'guest_list_enabled',
                'interested_count',
                'is_canceled',
                'is_draft',
                'is_page_owned',
                'maybe_count',
                'name',
                'noreply_count',
                'owner',
                'parent_group',
                'place',
                'scheduled_publish_time',
                'start_time,ticket_uri',
                'ticket_uri_start_sales_time',
                'ticketing_privacy_uri',
                'timezone',
                'type',
                'updated_time']

def main():
    """
        Call the facebook graph API to verify the access permission the events you created.
        Get the json data from all events you created, including all fields of an event.
        Output to "data.txt" file

    """
    print("Facebook Events Crawl Started.")
    graph = facebook.GraphAPI(access_token=ACCESS_TOKEN, version=API_VERSION)

    fields_param = ','.join(EVENT_FIELDS)
    event_data_list = graph.get_object('me?fields=events{'+fields_param+'}')

    with open('fb_event_data.json', 'w') as outfile:
        json.dump(event_data_list, outfile)

    print("Facebook Events Crawl Completed.")  
    
if __name__ == '__main__':
	main()