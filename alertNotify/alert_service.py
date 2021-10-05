#! /usr/bin/python3
import sys
import json
import cgi
import paho.mqtt.client as mqtt
import time, datetime, pytz
import threading
from tokenHandeler import generate_token, expired_token, check_dup, active_token, check_token
from sendmail import sendMail_alert, sendMail_shift, sendMail_esclate
from urllib import request, parse

# Contacts hard coded for the moment need to add this in a database.

contacts = {
    'stuart':{'email': 'stuart.ward.uk@gmail.com', 'phone': '447782325143'},
    'austin':{'email': 'austindangerjacobs@gmail.com', 'phone': '447505306153'},
    'jo':{'email': 'jo.ramsay@gmail.com', 'phone': '447576276209'},
    'rupert':{'email': 'rgw.smart@gmail.com', 'phone': '447951305579'},
    'tim':{'email': 'tim@milkreading.co.uk', 'phone': '447825303659'},
    'sophie':{'email':'sophie@fenwickpaul.com', 'phone': '447773767454'},
    'daniel':{'email': 'daniel.cameron@sky.com', 'phone': '447973656382'},
    'anita':{'email': 'anitapurser@hotmail.com', 'phone': '447914815343'},
    'neil':{'email': 'neilmaxbonner@hotmail.com', 'phone': '447767463321'}
    }

# table to keep a list of recent alert messages

alert_log_list = []

def log_alert_message(time: str, message: str) -> None:
    alert_log_list.append({'time': time, 'message': message})
    while len(alert_log_list) > 60:
        alert_log_list.remove(alert_log_list[0])
    return

# Read the google calendar to see who is on call

def calendar_read(api_key):
    SCOPE = 'https://www.googleapis.com/calendar/v3/calendars/'
    CALENDAR_ID = '6fue264k25k03v1ogsmkb2pk5g%40group.calendar.google.com'

# Dictionary of query parameters (if any)
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    parms = {
    'maxResults' : '20',
    'singleEvents' : 'true',
    'timeMin' : now,
    'key' : api_key
    }

    # Encode the query string
    querystring = parse.urlencode(parms)
    url =  SCOPE+CALENDAR_ID+'/events?'

    # Make a GET request and read the response
    requ = request.Request(url + querystring, headers={'Accept': 'application/json'})
    u = request.urlopen(requ)
    events =json.loads(u.read())
    oncall = []

    if not len(events['items']):
        print('No upcoming events found.', file=sys.stderr)
    else :
        for event in events['items']:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime' , event['end'].get('date'))
            print(start, end, event['summary'])
            if (start < now < end):
                print('oncall active',event['summary'], file=sys.stderr)
                entry = event['summary'].lower().split()
                if entry[0] in contacts:
                    oncall.append({'name': entry[0], 'role': entry[1], 'time': now})
    return oncall



def on_message(client, userdata, message):
    decoded_message = json.loads(message.payload)
    email1 = contacts.get(who_is_oncall.get('primary')).get('email')
    email2 = contacts.get(who_is_oncall.get('second')).get('email')
    alertMessage = decoded_message.get('MsgText')
    alertTime = decoded_message.get('TimeString')
    if not(check_dup(alertMessage)):
        token = generate_token(email1, 'At: {time} message: {message}'.format(time=alertTime, 
                                message=alertMessage), datetime.timedelta(seconds=15*60))
        sendMail_alert(email1,alertMessage,alertTime, token)
        sendMail_alert(email2,alertMessage,alertTime, token)
        log_alert_message(alertTime, alertMessage)
    return

def on_connect(client, userdata, flags, rc):
    if rc==0:
        client.subscribe(topic,qos)
        print("Connected and subscribed to ",topic)

    else:
        print("Connection fail")
    return

def on_log(client, userdata, level, buf):
#   print("log: ",buf, file=sys.stderr)
    return

# we are useing AWS Secrets Manager to hold API keys, and mqtt account password This retrieves a secret

import boto3

def get_secret(MySecretString):

    secret_name = "RdgHydroServerSecrets"
    region_name = "eu-west-2"

    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager',region_name=region_name)

    get_secret_value_response = client.get_secret_value(SecretId=secret_name)

    all_secret = json.loads(get_secret_value_response['SecretString'])
    secret = all_secret.get(MySecretString)
    return secret

# simple REST server to show whoisoncall and process acknolegements from email messages

def notfound_404(environ, start_response):
    start_response('404 Not Found', [ ('Content-type', 'text/plain') ])
    return [b'Not Found']

class PathDispatcher:
    def __init__(self):
        self.pathmap = { }

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO']
        params = cgi.FieldStorage(environ['wsgi.input'], environ=environ)
        method = environ['REQUEST_METHOD'].lower()
        environ['params'] = { key: params.getvalue(key) for key in params }
        handler = self.pathmap.get((method,path), notfound_404)
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
    start_response('200 OK', [ ('Content-type','text/html')])
    print(who_is_oncall, file=sys.stderr)
    resp = _oncall_resp.format(name1=who_is_oncall.get('primary'), name2=who_is_oncall.get('second'))
    yield resp.encode('utf-8')

_ack_resp_ok = '''\
<html>
  <head>
     <title>Reading Hydro On-Call</title>
   </head>
   <body>
     <h1>Acknowlegement of alert Sucessful</h1>
     <h1>Acknowlegement alerts currently active</h1>
     <table><tr><th>Token</th><th>Email address</th><th>Expiary Time</th><th>Status</th><th>Count</th><th>Message</th></tr>
     '''

_ack_resp_fail = '''\
<html>
  <head>
     <title>Reading Hydro On-Call</title>
   </head>
   <body>
     <h1>Acknowlegement of alert Failed</h1>
     <h1>Acknowlegement alerts currently active</h1>
     <table><tr><th>Token</th><th>Email address</th><th>Expiary Time</th><th>Status</th><th>Count</th><th>Message</th></tr>
     '''
_ack_list_body = '''\
    <tr><td><a href="http://readinghydro.org:8080/ackresp?token={token}">Token</a></td><td>{email}</td>
    <td>{time}</td><td>{status}</td><td>{count}</td><td>{message}</td></tr>
    '''
_ack_list_tail = '''\
    </table>
   </body>
</html>'''

def ackresp(environ, start_response):
    start_response('200 OK', [ ('Content-type', 'text/html')])
    params = environ['params']
    token = params.get('token')
    if check_token(token):
        resp = _ack_resp_ok
    else:
        resp = _ack_resp_fail
    tokenlist = active_token()
    for entry in tokenlist:
        status='Live'
        if entry.get('ack'): status='Acknowleged'
        resp = resp + _ack_list_body.format(token=entry.get('token'), email=entry.get('email'), 
                                            time=entry.get('time'), status=status, 
                                            count=entry.get('count'), message=entry.get('message'))
    resp = resp + _ack_list_tail
    yield resp.encode('utf-8')

_alert_list_head = '''\
<html>
  <head>
     <title>Reading Hydro On-Call</title>
   </head>
   <body>
     <h1>Alert history</h1>
     <table><tr><th>Time</th><th>Message</th></tr>
     '''
_alert_list_body = '''\
    <tr><td>{time}</td><td>{message}</td></tr>
    '''
_alert_list_tail = '''\
    </table>
   </body>
</html>'''

def alertlist(environ, start_response):
    start_response('200 OK', [ ('Content-type', 'text/html')])
    tokenlist = active_token()
    resp = _alert_list_head
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

tz_london = pytz.timezone('Europe/London')
now = datetime.datetime.now(tz_london)
now_string = now.strftime('%Y-%m-%dT%H:%M:%S')
log_alert_message(now_string, 'Alert Service startup')

# This section starts the mqtt subscribe thread

mqtt_broker = 'readinghydro.org'
mqtt_broker_port = 8883
topic = "hydro-alert"
qos=0
last_hour = -1

client = mqtt.Client("purple")

client.username_pw_set("mqttrota",get_secret('MQTT_ROTA_PWD'))
client.on_connect = on_connect
client.on_message = on_message
client.on_log = on_log
client.tls_set("/etc/ssl/certs/ca-certificates.crt")
who_is_oncall = {'primary' : '', 'second': ''}

got_api_data = True
latest_data_time = datetime.datetime.utcnow()
latest_data = latest_data_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
next_data_report_time = datetime.datetime.utcnow()

google_api_key = get_secret('GOOGLE_API_KEY')

try:
    client.connect(mqtt_broker, mqtt_broker_port)
    print("connecting to mqtt broker", mqtt_broker, file=sys.stderr)
    client.loop_start()

except:
    print("mqtt broker connection failed", file=sys.stderr)

# Start the restServer in another thread

restThread = threading.Thread(target=restServer, daemon=True)
restThread.start()

# read the calendar once an hour, if there is an entry for each of the roles update the current role person
# if there is no new entry for a role the old entry will be kept

try:
    while True:
        now_utc = datetime.datetime.utcnow()
        now = datetime.datetime.now(tz_london)
        now_utc_string = now.strftime('%Y-%m-%dT%H:%M:%SZ')
        now_string = now.strftime('%Y-%m-%dT%H:%M:%S')
        if last_hour != now.hour:
            last_hour = now.hour
            new_who_is_oncall = calendar_read(google_api_key)
            print(new_who_is_oncall)
            for role in ('primary', 'second'):
                for person in new_who_is_oncall:
                    if person['role'] == role:
                        who_is_oncall.update({role: person.get('name')})
                if last_hour == 9:
                    email = contacts.get(who_is_oncall.get(role)).get('email')
                    message='Sending oncall reminder to '+ who_is_oncall.get(role)+ ' at '+email+' for role '+role
                    sendMail_shift(email, role, generate_token(email, message, datetime.timedelta(seconds=15*60)))
                    log_alert_message(now_string, message)

# look through the alert list for any expited alerts that have not been acknowleged.
# or entries that record repeated events even if acknowleged

        tokenlist = expired_token()
        for entry in tokenlist:
            if entry.get('count') == 0:
                sendMail_esclate('alerts@readinghydro.org', 'Esculate: '+entry.get('message'))
            else:
                email1 = contacts.get(who_is_oncall.get('primary')).get('email')
                email2 = contacts.get(who_is_oncall.get('second')).get('email')
                dup_count = entry.get('count')
                alertMessage = 'Repeated: {count} message: {message}'.format(count=dup_count, message=entry.get('message'))
                token = generate_token(email1, alertMessage, datetime.timedelta(seconds=15*60))
                sendMail_alert(email1,alertMessage,now_utc_string, token)
                sendMail_alert(email2,alertMessage,now_utc_string, token)
                log_alert_message(now_string, alertMessage)

# check the data feeds to see if we have current data, if not raise an alert

        try:
            latest_request = request.urlopen('https://readinghydro.org:9445/api/plc/current')
        except:
            if got_api_data:
                log_alert_message(now_string, 'Failed to get API data, Latest data at: '+latest_data)
                got_api_data = False
        else:
            got_api_data = True
            latest_data = json.loads(latest_request.read())
            latest_data_time = datetime.datetime.strptime(latest_data.get('received_at'), '%Y-%m-%dT%H:%M:%S.%fZ')

        if latest_data_time < now_utc - datetime.timedelta(seconds=20*60):
            if now_utc > next_data_report_time:
                next_data_report_time = now_utc + datetime.timedelta(seconds=15*60)
                email1 = contacts.get(who_is_oncall.get('primary')).get('email')
                email2 = contacts.get(who_is_oncall.get('second')).get('email')
                alertMessage = 'No data recieved since '+latest_data_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                alertMessage += ' That is {minutes:.2} Minutes ago'.format(minutes=(now_utc-latest_data_time).seconds/60)
                token = generate_token(email1, 'At: {time} message: {message}'.format(time=now_string, message=alertMessage), datetime.timedelta(seconds=15*60))
                sendMail_alert(email1,alertMessage,now_string, token)
                sendMail_alert(email2,alertMessage,now_string, token)
                log_alert_message(now_string, alertMessage)

# check the REST server is running, restart it if not
        if not(restThread.is_alive()):
            print('Restarting rest Server', file=sys.stderr)
            log_alert_message(now_string, 'Restarting REST server')
            restThread.start()

        time.sleep(10)
        pass

except KeyboardInterrupt:
    print("interrrupted by keyboard", file=sys.stderr)

log_alert_message(now_string, 'Alert Service shutdown')

client.loop_stop() #stop loop
time.sleep(5)
