
# Alert and Notify #

This subsystem provides menagement and escallation of Alerts recieved from the Reading Hydro control system.

## Installation Requirements ##

The Google calendar APIs allow reading of the calendar entries for a day with

``` bash
curl   'https://www.googleapis.com/calendar/v3/calendars/6fue264k25k03v1ogsmkb2pk5g%40group.calendar.google.com/events?key=API_KEY'   --header 'Accept: application/json'
```

The Calendar ID is in this case [6fue264k25k03v1ogsmkb2pk5g@group.calendar.google.com]

for the google Interface library install
pip install google_auth_oauthlib google-api-python-client
sudo apt install python3-googleapi python3-google-auth-oauthlib

for the MQTT library
pip install paho-mqtt
sudo apt install python3-paho-mqtt

for the EADataCollector
sudo apt install python3-psycopg2

## Modules ##

These modules provide the Alert notification system for Reading Hydro On-Call team

### alert_service ###

This is the main module that should be started, It contains the REST server and the mqtt topic subscriber and calandar_read.

### calendar_read ###

The calendar read module reads the google calendar and finds the on call entries current. If none the last on call enterirs are kept till a new oncall event starts.
Calender Events must have the subject in the form "Name role", where role is either Primary or Second

An on shift reminder email is sent at about 9:00 each day to the current on-call primary and second. These will need to be acknowleged or they will be escalated to the [alerts@readinghydro.org] group.

### mqtt-topic ###

The mqtt-topic attached to the readinghydro.org mosquitto broker and subscribes to the "hydro-alert" topic when an alert is recieved an email is sent to the primary and secondary on-call person. These contain a token to confirm recipt of the message. If the token is not acknowleged in 5 minutes a escalation email is sent to [alerts@readinghydro.org]

### restServer ###

restServer provides a simple http webserver on port 8080 the respondes to:

[/whoisoncall](http://readinghydro.org:8080/whoisoncall)  Shows the on call primary and second person

[/ackresp?token=](http://readinghydro.org:8080/ackresp?token=)   process the acknologements frm emails sent

[/alertlist](http://readinghydro.org:8080/alertlist)   shows all the active tokens and wether they have been acknowleged

### tokenHandler ###

Generates the tokens, and provides methods to list, and acknlowege the tokens

### sendmail ###

Sends the various alert and esclation emails. No longer used, events are sent with ntfy

### sendntfy ###

Send alert messages to the ntfy channel "alerts-readinghydro-org"

## To Do ##

1. Connect to the TTN network to revieve smoke alarm and door status
2. Add TLS to the restServer. Not done proxy through apache to achieve this.
