#! /usr/bin/python3

from __future__ import print_function
import datetime
from syslog import syslog
import json
import boto3
from urllib import request, parse


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SERVICE_ACCOUNT_FILE = 'credentials.json'
CALENDAR_ID = '6fue264k25k03v1ogsmkb2pk5g@group.calendar.google.com'

def get_secret(MySecretString):

    secret_name = "RdgHydroServerSecrets"
    region_name = "eu-west-2"

    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    get_secret_value_response = client.get_secret_value(SecretId=secret_name)

    all_secret = json.loads(get_secret_value_response['SecretString'])
    secret = all_secret.get(MySecretString)
    return secret

def calendar_read(api_key):
    SCOPE = 'https://www.googleapis.com/calendar/v3/calendars/'
    CALENDAR_ID = '6fue264k25k03v1ogsmkb2pk5g%40group.calendar.google.com'

# Dictionary of query parameters
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    now_end = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat() + 'Z'
    parms = {
        'maxResults': '10',
        'singleEvents': 'true',
        'timeMin': now,
        'timeMax': now_end,
        'key': api_key
    }

    # Encode the query string
    querystring = parse.urlencode(parms)
    url = SCOPE+CALENDAR_ID+'/events?'

    # Make a GET request and read the response
    requ = request.Request(url + querystring, headers={'Accept': 'application/json'})
    u = request.urlopen(requ)
    events = json.loads(u.read())
    oncall = []

    if not len(events['items']):
        syslog.syslog('No upcoming events found.')
    else:
        for event in events['items']:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            if (start < now < end):
                entry = event['summary'].lower().split()
                oncall.append({'name': entry[0], 'role': entry[1], 'time': now})
    return oncall


def main():
    print('Google Calendar API Test')
    google_api_key = get_secret('GOOGLE_API_KEY')
    oncall = calendar_read(google_api_key)
    print(oncall)
    return
    
if __name__ == '__main__':
    main()
