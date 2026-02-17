#! /usr/bin/python3
import syslog
import json
import cgi
from urllib.error import HTTPError, URLError
from socket import timeout as TimeoutError
import paho.mqtt.client as mqtt
import time
import datetime
import pytz
import threading
import boto3
from tokenHandeler import generate_token, expired_token, check_dup, active_token, check_token, token_mark_sent
from urllib import request, parse
from sendntfy import sendntfy

# timing parameters

NO_DATA_REPORT_EVENT = datetime.timedelta(minutes=20)
NO_DATA_RE_REPORT_TIME = datetime.timedelta(hours=6)
ALERT_ESCALATION_TIME = datetime.timedelta(minutes=15)
ONCALL_ESCALATION_TIME = datetime.timedelta(minutes=150)
IGNORE_ALERTS_OLDER_THAN = datetime.timedelta(minutes=10)
# table to keep a list of recent alert messages

alert_log_list = []


def log_alert_message(time: str, message: str) -> None:
    syslog.syslog('alert: ' + time + ' ' + message)
    alert_log_list.append({'time': time, 'message': message})
    while len(alert_log_list) > 30:
        alert_log_list.remove(alert_log_list[0])
    return

# Read the google calendar to see who is on call


def calendar_read(api_key):
    SCOPE = 'https://www.googleapis.com/calendar/v3/calendars/'
    CALENDAR_ID = '6fue264k25k03v1ogsmkb2pk5g%40group.calendar.google.com'

# Dictionary of query parameters
    now = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    now_end = (datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
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
                if entry[0] in contacts:
                    oncall.append({'name': entry[0], 'role': entry[1], 'time': now})
                    syslog.syslog('oncall active ' + event['summary'])
    return oncall


def on_message(client, userdata, message):
    decoded_message = json.loads(message.payload)
    email1 = contacts.get(who_is_oncall.get('primary')).get('email')
    alertMessage = decoded_message.get('MsgText')
    alertTime = decoded_message.get('TimeString')
    if decoded_message.get('StateAfter') == "0":
        alertMessage = 'Cleared: ' + alertMessage
    else:
        alertMessage = 'Active: ' + alertMessage
    syslog.syslog('mqtt message: ' + message.payload.decode("utf-8"))
    try:
        alert_time_data = datetime.datetime.strptime(alertTime, '%d/%m/%Y %H:%M:%S')
    except ValueError:
        alert_time_string = alertTime
        alert_age = datetime.timedelta(seconds=1)
        alert_time_data = datetime.datetime.now(datetime.UTC)
        alert_time_data = alert_time_data.replace(tzinfo=datetime.timezone.utc)
    else:
        alert_time_string = datetime.datetime.strftime(alert_time_data, '%Y-%m-%dT%H:%M:%S')
        compare_now = datetime.datetime.strptime(datetime.datetime.now(datetime.UTC).strftime('%d/%m/%Y %H:%M:%S'), '%d/%m/%Y %H:%M:%S')
        alert_age = compare_now - alert_time_data
    if alert_age < IGNORE_ALERTS_OLDER_THAN:
        log_alert_message(alert_time_string, alertMessage)
        if not(check_dup(alertMessage)):
            token = generate_token(email1, alertMessage, ALERT_ESCALATION_TIME)
            sendntfy(alertMessage, alert_time_data, token)
    else:
        if not(check_dup('Ignoring old alerts')):
            token = generate_token(email1, 'Ignoring old alerts', ALERT_ESCALATION_TIME)
            sendntfy('Ignoring old alerts', datetime.datetime.now(datetime.UTC), token)
            check_token(token)
    return


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(topic, qos)
        syslog.syslog("Connected and subscribed to " + topic)

    else:
        syslog.syslog("Connection fail")
    return


def on_log(client, userdata, level, buf):
    #   syslog.syslog("log: " + buf)
    return


# we are useing AWS Secrets Manager to hold API keys, and mqtt account password This retrieves a secret


def get_secret(MySecretString):

    secret_name = "RdgHydroServerSecrets"
    region_name = "eu-west-2"

    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    get_secret_value_response = client.get_secret_value(SecretId=secret_name)

    all_secret = json.loads(get_secret_value_response['SecretString'])
    secret = all_secret.get(MySecretString)
    return secret

# simple REST server to show whoisoncall and process acknolegements from email messages


def notfound_404(environ, start_response):
    start_response('404 Not Found', [('Content-type', 'text/plain')])
    return [b'Not Found']


class PathDispatcher:
    def __init__(self):
        self.pathmap = {}

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO']
        params = cgi.FieldStorage(environ['wsgi.input'], environ=environ)
        method = environ['REQUEST_METHOD'].lower()
        environ['params'] = {key: params.getvalue(key) for key in params}
        handler = self.pathmap.get((method, path), notfound_404)
        return handler(environ, start_response)

    def register(self, method, path, function):
        self.pathmap[method.lower(), path] = function
        return function


_oncall_resp = '''\
<html>
  <head>
     <title>Reading Hydro On-Call</title>
   </head>
   <body>
     <h1>Current on call Primary contact is {name1}</h1>
     <h1>Current on call Secondary contact is {name2}</h1>
   </body>
</html>'''


def whoisoncall(environ, start_response):
    start_response('200 OK', [('Content-type', 'text/html')])
    syslog.syslog('who is oncall ')
    resp = _oncall_resp.format(name1=who_is_oncall.get('primary'), name2=who_is_oncall.get('second'))
    yield resp.encode('utf-8')


_ack_resp_ok = '''\
<html>
  <head>
     <title>Reading Hydro Alert Acknowledgement</title>
     <meta http-equiv="refresh" content="600">
   </head>
   <body>
     <h1>Acknowledgement of alert Sucessful</h1>
     <h1>Acknowledgement alerts currently active</h1>
     <table><tr><th>Token</th><th>Email address</th><th>Expiary Time</th><th>Status</th><th>Count</th><th>Message</th></tr>
     '''


_ack_resp_fail = '''\
<html>
  <head>
     <title>Reading Hydro Alert Acknowledgement</title>
     <meta http-equiv="refresh" content="600">
   </head>
   <body>
     <h1>Acknowledgement of alert Failed</h1>
     <h1>Acknowledgement alerts currently active</h1>
     <table><tr><th>Token</th><th>Email address</th><th>Expiary Time</th><th>Status</th><th>Count</th><th>Message</th></tr>
     '''
_ack_list_body = '''\
    <tr><td><a href="https://readinghydro.org/ackresp?token={token}">Token</a></td><td>{email}</td>
    <td>{time}</td><td>{status}</td><td>{count}</td><td>{message}</td></tr>
    '''
_ack_list_tail = '''\
    </table>
   </body>
</html>'''


def ackresp(environ, start_response):
    start_response('200 OK', [('Content-type', 'text/html')])
    params = environ['params']
    token = params.get('token')
    if check_token(token):
        resp = _ack_resp_ok
    else:
        resp = _ack_resp_fail
    tokenlist = active_token()
    for entry in tokenlist:
        status = 'Live'
        if entry.get('ack'):
            status = 'Acknowledged'
        resp = resp + _ack_list_body.format(token=entry.get('token'),
                                            email=entry.get('email'),
                                            time=entry.get('time'), 
                                            status=status,
                                            count=entry.get('count'), 
                                            message=entry.get('message'))
    resp = resp + _ack_list_tail
    yield resp.encode('utf-8')


_alert_list_head = '''\
<html>
  <head>
     <title>Reading Hydro Alert Activity</title>
     <meta http-equiv="refresh" content="600">
   </head>
   <body>
     <h1>Alert history at {time}</h1>
     <table><tr><th>Time</th><th>Message</th></tr>
     '''
_alert_list_body = '''\
    <tr><td>{time} </td><td>{message}</td></tr>
    '''
_alert_list_tail = '''\
    </table>
   </body>
</html>'''


def alertlist(environ, start_response):
    start_response('200 OK', [('Content-type', 'text/html')])
    tokenlist = active_token()
    resp = _alert_list_head.format(time=datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%dT%H:%M:%SZ'))
    for entry in alert_log_list:
        resp = resp + _alert_list_body.format(time=entry.get('time'), message=entry.get('message'))
    resp = resp + _alert_list_tail
    yield resp.encode('utf-8')


def restServer():
    from wsgiref.simple_server import make_server

    # Create the dispatcher and register functions
    dispatcher = PathDispatcher()
    dispatcher.register('GET', '/whoisoncall', whoisoncall)
    dispatcher.register('GET', '/ackresp', ackresp)
    dispatcher.register('GET', '/alertlist', alertlist)

    # Launch a basic server
    httpd = make_server('', 8080, dispatcher)
    httpd.serve_forever()
    return

# System startup
# get the contacts data from the config file /etc/hydro/oncall-contacts.cfg


f = open('/etc/hydro/oncall-contacts.cfg', 'r')
contactsJSON = f.read(-1)
contacts = json.loads(contactsJSON)
f.close()

tz_london = pytz.timezone('Europe/London')
now = datetime.datetime.now(tz_london)
now_string = now.strftime('%Y-%m-%dT%H:%M:%S')
sendntfy("Alert Service Startup", datetime.datetime.now(datetime.UTC), "")
log_alert_message(now_string, 'Alert Service startup')

# This section starts the mqtt subscribe thread

mqtt_broker = 'readinghydro.org'
mqtt_broker_port = 8883
topic = "hydro-alert"
qos = 0
last_hour = -1

client = mqtt.Client("purple")

client.username_pw_set("mqttrota", get_secret('MQTT_ROTA_PWD'))
client.on_connect = on_connect
client.on_message = on_message
client.on_log = on_log
client.tls_set("/etc/ssl/certs/ca-certificates.crt")

# set the time and oncall initial values

who_is_oncall = {'primary': 'Unknown', 'second': 'Unknown'}
got_api_data = False
latest_data_time = datetime.datetime.now(datetime.UTC)
latest_data_time = latest_data_time.replace(tzinfo=datetime.timezone.utc)
latest_data = latest_data_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
next_data_report_time = datetime.datetime.now(datetime.UTC)
next_data_report_time = next_data_report_time.replace(tzinfo=datetime.timezone.utc)

google_api_key = get_secret('GOOGLE_API_KEY')

# Start the mqtt subscribe loop

try:
    client.connect(mqtt_broker, mqtt_broker_port)
    syslog.syslog("connecting to mqtt broker " + mqtt_broker)
    client.loop_start()

except:
    syslog.syslog("mqtt broker connection failed")
    log_alert_message(now_string, "mqtt broker connection failed")

# Start the restServer in another thread

restThread = threading.Thread(target=restServer, daemon=True)
restThread.start()

# read the calendar once an hour, if there is an entry for each of the roles update the current role person
# if there is no new entry for a role the old entry will be kept

while True:
    alertMessages = []
    escalateMessages = []

    now_utc = datetime.datetime.now(datetime.UTC)
    now_utc = now_utc.replace(tzinfo=datetime.timezone.utc)
    now = datetime.datetime.now(tz_london)
    now_utc_string = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    now_string = now.strftime('%Y-%m-%dT%H:%M:%S')

# every hour read the calendar and see if there is a change in oncall personel

    if last_hour != now.hour:
        last_hour = now.hour
        new_who_is_oncall = calendar_read(google_api_key)
        for role in ('primary', 'second'):
            for person in new_who_is_oncall:
                if person['role'] == role:
                    if person.get('name') != who_is_oncall.get(role):
                        who_is_oncall.update({role: person.get('name')})
                        message = "On-Call for {role} is now {name}".format(role=role, name=person.get('name'))
                        sendntfy(message, now, "")
                        log_alert_message(now_string, message)
            if last_hour == 7:
                email = contacts.get(who_is_oncall.get(role)).get('email')
                message = 'Sending oncall reminder to ' + who_is_oncall.get(role) + ' for role ' + role
                token = generate_token(email, message, ONCALL_ESCALATION_TIME)
                sendntfy(message, now, token)
                token_mark_sent(token)
                log_alert_message(now_string, message)

# look through the alert list for any expired alerts that have not been acknowleged.
# or entries that record repeated events even if acknowleged

    email1 = contacts.get(who_is_oncall.get('primary')).get('email')
    email2 = contacts.get(who_is_oncall.get('second')).get('email')

    tokenlist = expired_token()
    for entry in tokenlist:
        if entry.get('count') == 0:
            escalateMessages.append('Escalate: ' + entry.get('message'))
            sendntfy('Escalate: ' + entry.get('message'), now, "")
        else:
            dup_count = entry.get('count')
            alertMessage = 'Repeated: {count:d} message: {message}'.format(count=dup_count, message=entry.get('message'))
            token = generate_token(email1, alertMessage, ALERT_ESCALATION_TIME)
            alertMessages.append(alertMessage)
            sendntfy(alertMessage, now, "")
            log_alert_message(now_string, alertMessage)

    tokenlist = active_token()
    for entry in tokenlist:
        if not(entry.get('sent')):
            alertMessages.append(entry.get('message'))
            token = entry.get('token')
            token_mark_sent(token)
    
# check the data feeds to see if we have current data, if not raise an alert

    try:
        latest_request = request.urlopen('https://readinghydro.org/api/plc/current', timeout=6)
    except (HTTPError, URLError, TimeoutError) as error:
        got_api_data = False
        syslog.syslog('Data not retrieved because of {error}'.format(error=error))
    else:
        got_api_data = True
        latest_data = json.loads(latest_request.read())
        latest_data_time = datetime.datetime.strptime(latest_data.get('received_at'), '%Y-%m-%dT%H:%M:%SZ')
        latest_data_time = latest_data_time.replace(tzinfo=datetime.timezone.utc)

    if latest_data_time < now_utc - NO_DATA_REPORT_EVENT:
        if now_utc > next_data_report_time:
            next_data_report_time = now_utc + NO_DATA_RE_REPORT_TIME
            alertMessage = 'No data received since '+latest_data_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            alertMessage += ' That is {minutes:5.2f} Minutes ago'.format(minutes=(now_utc-latest_data_time).seconds/60)
            token = generate_token(email1, 'At: {time} message: {message}'.format(time=now_string, message=alertMessage),
                                    datetime.timedelta(seconds=15*60))
            alertMessages.append(alertMessage)
            sendntfy("Active " + alertMessage, now, token)
            log_alert_message(now_string, alertMessage)

# check the REST server is running, restart it if not
    if not(restThread.is_alive()):
        syslog.syslog('Restarting rest Server ')
        log_alert_message(now_string, 'Restarting REST server')
        restThread.start()

    time.sleep(30)
    pass


log_alert_message(now_string, 'Alert Service shutdown')

client.loop_stop()     # stop loop
time.sleep(5)
