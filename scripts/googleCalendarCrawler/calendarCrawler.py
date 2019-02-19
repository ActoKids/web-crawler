from __future__ import print_function
import datetime
import pickle
import os.path
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from httplib2 import Http
from oauth2client import file, client, tools

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
OUTPUT = {} #Instantiate an empty OUTPUT JSON object

def create_json():
    with open('calendar_event_data.json', 'w') as outfile:
        json.dump(OUTPUT, outfile)

def main():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    
    events_result = service.events().list(calendarId='ejohnson98396@gmail.com', timeMin=now, maxResults=100, singleEvents=True, orderBy='startTime').execute() 
    # creates a list of event objects from a particular calendar, specified by id
    # Does not show every occurence of a recurring event, just the most recent one
    # Max results of 100 individual events

    # user_calendars = service.calendarList().list(syncToken=None, minAccessRole=None, maxResults=None, showDeleted=None, showHidden=None, pageToken=None).execute()
    ### Output shows all calendars on the users account and their info, like the id called for events_result
    
    events = events_result.get('items', []) 
    # Instantiates an event object to be used for parsing

    print('Starting GoogleCalendar crawler; ', datetime.datetime.now())

    if len([events]) > 0:
        print('Opening calendars: Success')
        # If calendar has objects run the program
    if len([events]) < 1:
        print('Opening calendars: Fail')
        quit()
        # If calendar is empty kill the program

    if not events:
        print('No upcoming events found.') 
        # If events is empty, script will not run
    for event in events:
        try:
            OUTPUT[event['summary']] = {"Title": event['summary'], 'Description': event['description'], 'Email': event['organizer'].get('email'), 'Date': event['start'].get('date'), 'Start Time': event['start'].get('dateTime'), 'End Time': event['end'].get('dateTime'), 'Status': event['status'], 'Location': event['location'], 'URL': event['htmlLink']}
            # Creates a JSON object of event and its details
        except KeyError:
            OUTPUT[event['summary']] = {"Title": event['summary'], 'Description': event['description'], 'Email': event['organizer'].get('email'), 'Date': event['start'].get('date'), 'Start Time': event['start'].get('dateTime'), 'End Time': event['end'].get('dateTime'), 'Status': event['status'], 'Location': 'null', 'URL': event['htmlLink']}
            # If location data is unusable, default to null
            # Will later search in the description for a location, or leave this field null if location cannot be found
            
    create_json()
    print("Closing GoogleCalendar crawler; ", datetime.datetime.now())

if __name__ == '__main__':
    main()