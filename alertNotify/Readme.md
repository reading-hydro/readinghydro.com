
The Google calendar APIs allow readind of the calendar entries for a day with 

curl   'https://www.googleapis.com/calendar/v3/calendars/6fue264k25k03v1ogsmkb2pk5g%40group.calendar.google.com/events?key=API_KEY'   --header 'Accept: application/json'

The Calendar ID is in this case 6fue264k25k03v1ogsmkb2pk5g@group.calendar.google.com

for the google Interface library install only needed if useing calendarreadgoogle.pv
pip install google_auth_oauthlib google-api-python-client

for the MQTT library
pip install paho-mqtt

