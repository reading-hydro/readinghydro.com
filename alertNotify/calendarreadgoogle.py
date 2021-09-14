from __future__ import print_function
import datetime
from googleapiclient.discovery import build
from google.oauth2 import service_account


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SERVICE_ACCOUNT_FILE = 'credentials.json'
CALENDAR_ID = '6fue264k25k03v1ogsmkb2pk5g@group.calendar.google.com'

def create_service():
  credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
  delegated_credentials = credentials.with_subject('oncall-notification-demon@vertical-jigsaw-276509.iam.gserviceaccount.com')

  service_name = 'calendar'
  api_version = 'v3'
  service = build(
    service_name,
    api_version,
    credentials=delegated_credentials)

  return service

def main():

    service = create_service()

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming events')
    events_result = service.events().list(calendarId=CALENDAR_ID, timeMin=now,
                                        maxResults=3, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime' , event['end'].get('date'))
        if (start < now < end):
            print('oncall active',event['summary'])

if __name__ == '__main__':
    main()