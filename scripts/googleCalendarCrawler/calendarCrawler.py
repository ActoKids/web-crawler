from __future__ import print_function
import datetime
import json
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
OUTPUT = {}

def create_json():
    with open('calendar_event_data.json', 'w') as outfile:
        json.dump(OUTPUT, outfile)

def main():
    print("Google Calendar Crawl Started.")
    global OUTPUT
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('calendar', 'v3', http=creds.authorize(Http()))

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=20, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        try:
            OUTPUT[event['summary']] = {"Title": event['summary'], "Time": event['start'].get('dateTime'), "Date": event['start'].get('date'), "Location": event['location'], "Description": event['description'], "Email": email}
        except UnicodeEncodeError:
            print('Event data not found')
        except KeyError:
            print('Event data not published')
    create_json()
    print("Google Calendar Crawler Completed.")

if __name__ == '__main__':
    main()
