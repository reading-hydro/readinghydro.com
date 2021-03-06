#! /usr/bin/python3

from urllib import request, parse
import datetime
import json


def calendarread(api_key):
    # If modifying these scopes, delete the file token.json.
    SCOPE = 'https://www.googleapis.com/calendar/v3/calendars/'
    CALENDAR_ID = '6fue264k25k03v1ogsmkb2pk5g%40group.calendar.google.com'

# Dictionary of query parameters (if any)
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    parms = {
        'maxResults': '5',
        'singleEvents': 'true',
        'timeMin': now,
        'key': api_key
    }

    # Encode the query string
    querystring = parse.urlencode(parms)
    url = SCOPE + CALENDAR_ID + '/events?'
    oncall = []

    # Make a GET request and read the response
    try:
        requ = request.Request(url + querystring, headers={'Accept': 'application/json'})
        u = request.urlopen(requ, timeout=3)
    except:
        return oncall
    events = json.loads(u.read())

    if not len(events['items']):
        print('No upcoming events found.')
    else:
        for event in events['items']:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            if (start < now < end):
                print('oncall active', event['summary'])
                entry = event['summary'].lower().split()
                oncall.append({'name': entry[0], 'role': entry[1], 'time': now})
    return oncall
