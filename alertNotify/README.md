
# Alert and Notify #

This subsystem provides menagement and escallation of Alerts recieved from the Reading Hydro control system. 

# Installation Requirements #

The Google calendar APIs allow reading of the calendar entries for a day with 

```
curl   'https://www.googleapis.com/calendar/v3/calendars/6fue264k25k03v1ogsmkb2pk5g%40group.calendar.google.com/events?key=API_KEY'   --header 'Accept: application/json'
```

The Calendar ID is in this case 6fue264k25k03v1ogsmkb2pk5g@group.calendar.google.com

for the google Interface library install only needed if useing calendarreadgoogle.py
pip install google_auth_oauthlib google-api-python-client

for the MQTT library
pip install paho-mqtt

# Modules #

These modules provide the Alert notification system for Reading Hydro On-Call team

## Calendarread ##

The calendar read module reads the google calendar and finds the on call entries current. If none the last on call enterirs are kept till a new oncall event starts. 
Calender Events must have the subject in the form "Name role", where role is either Primary or Second

An on shift reminder email is sent at about 9:00 each day to the current on-call primary and second.

## mqtt-topic ##

The mqtt-topic attached to the readinghydro.org mosquitto broker and subscribes to the "hydro-alert" topic when an alert is recieved an email is sent to the 
primary and secondary on-call person. These contain a token to confirm recipt of the message. If the token is not acknowleged in 5 minutes a escalation email 
is sent to alerts@readinghydro.org

## restServer ##

restServer provides a simple http webserver on port 8080 the respondes to:

[/whoisoncall](http://readinghydro.org/whoisoncall)  Shows the on call primary and second person

[/ackresp?token=](http://readinghydro.org/ackresp?token=)   process the acknologements frm emails sent

[/alertlist](http://readinghydro.org/alertlist)   shows all the active tokens and wether they have been acknowleged

## tokenHandler ##

generates the tokens, and provides methods to list, and acknlowege the tokens

## sendmail ##

sends the various alert and esclation emails
