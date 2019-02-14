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
OUTPUT = {}

def create_json():
    with open('calendar_event_data.json', 'w') as outfile:
        json.dump(OUTPUT, outfile)


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
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
    print('Getting the upcoming 100 events')
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=100, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        email = event['creator'].get('email', event['creator'].get('email'))
        try:
            OUTPUT[event['summary']] = {"Title": event['summary'], "Time": event['start'].get('dateTime'), "Date": event['start'].get('date'), "Location": event['location'], "Description": event['description'], "Email": email}
            # Output goes to a JSON file called calendar_event_data.json
            # Tested by Michael Leon
            # He tested the output of the code. Most of the data was unstructured but the 'Title', Time', 'Date', and 'Location' we consistently accurate. The 'Description' often had these other fields included.
            # The 'Email' was associated with the email of the current calendar, so adding all the calendars together created a single email for this field.
        except UnicodeEncodeError:
            print('Event data not found')
            # Much of the data is not encoded in 'UTF-8', which throws this error.
        except KeyError:
            print('Event data not published')
            # KeyError happens if one of the fields is unpublished (usually the location).

    create_json()
    print(json.dumps(OUTPUT, indent=4, sort_keys=True))
    # Printing is for testing purposes, will not be the final version.
    print("Google Calendar Crawler Completed.")

if __name__ == '__main__':
    main()