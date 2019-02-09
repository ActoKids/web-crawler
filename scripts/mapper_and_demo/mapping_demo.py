# -*- coding: utf-8 -*-
"""
Created on 02/3/2019
NSC - AD440 CLOUD PRACTICIUM
@author: Nick Bennett
"""
import json


# CONTAINS THE CURRENT MAPPINGS. 
MAPPING_DICTIONARY = {
    "Title": "name",
    "Date": "start_time",
    "Location": "location_address",
    "Description": "description",
    "Price": "cost"
}

"""
process_unmapped_json opens a file that contains the JSON
this is so I do not need to download the same JSON repeated
from the target website.

The demo JSON was made with Mikes Eventbrite Crawler.

First the JSON is loaded, then it's keys are broken down.
In these case we need to break down two layers of keys to get
to the data we want. We organize the new data with the corrected
key value pairs into temp_data. That data is added to mapped_json
which will be our final JSON.

This could be improved by removing the need to have a key for mapped_json.
"""
def process_unmapped_json():
    with open('browser_event_data.json', 'r') as output:
        unmapped_json = json.load(output)
        mapped_json = {}
        integer_key = 0
        for first_key in unmapped_json.keys():
            temp_data = {}
            for second_key in unmapped_json[first_key].keys():
                temp_data[remapping_protocol(second_key)] = unmapped_json[first_key][second_key]
            mapped_json[integer_key] = temp_data
            integer_key = integer_key + 1
        print(json.dumps(mapped_json))


"""
remapping_protocol is pretty staight forward.

First the old key is checked to see if it is in our current MAPPING_DICTIONARY.
If so, then the new_key is returned. Otherwise a blank is returned,
where the blank may be a default value that is yet to be assigned.
"""
def remapping_protocol(old_key):
    new_key = ""
    if old_key in MAPPING_DICTIONARY:
        new_key = MAPPING_DICTIONARY[old_key]
    return new_key


def main():
    process_unmapped_json()

    
if __name__ == '__main__':
	main()
