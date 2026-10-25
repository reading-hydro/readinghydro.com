#! /usr/bin/python3
import datetime
import json
import syslog
import time
from socket import timeout as TimeoutError
from urllib import parse, request
from urllib.error import HTTPError, URLError

import boto3
import paho.mqtt.client as mqtt
import pytz

from sendntfy import sendntfy
from shared_state import (
    append_alert_log,
    get_on_call_person,
    update_on_call_person,
)
from tokenHandeler import (
    active_token,
    check_dup,
    check_token,
    expired_token,
    generate_token,
    token_mark_sent,
)

NO_DATA_REPORT_EVENT = datetime.timedelta(minutes=20)
NO_DATA_RE_REPORT_TIME = datetime.timedelta(hours=6)
ALERT_ESCALATION_TIME = datetime.timedelta(minutes=15)
ONCALL_ESCALATION_TIME = datetime.timedelta(minutes=150)
IGNORE_ALERTS_OLDER_THAN = datetime.timedelta(minutes=10)

MQTT_BROKER = 'readinghydro.org'
MQTT_BROKER_PORT = 8883
MQTT_TOPIC = 'hydro-alert'
MQTT_QOS = 0


def log_alert_message(timestamp, message):
    syslog.syslog('alert: ' + timestamp + ' ' + message)
    append_alert_log(timestamp, message)


def calendar_read(api_key, calendar_id, contacts):
    scope = 'https://www.googleapis.com/calendar/v3/calendars/'
    now = datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    now_end = (datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    params = {
        'maxResults': '10',
        'singleEvents': 'true',
        'timeMin': now,
        'timeMax': now_end,
        'key': api_key,
    }
    querystring = parse.urlencode(params)
    url = scope + calendar_id + '/events?'
    calendar_request = request.Request(url + querystring, headers={'Accept': 'application/json'})
    with request.urlopen(calendar_request) as response:
        events = json.loads(response.read())

    oncall = []
    if not events['items']:
        syslog.syslog('No upcoming events found.')
    else:
        for event in events['items']:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            if start < now < end:
                entry = event['summary'].lower().split()
                if entry[0] in contacts:
                    oncall.append({'name': entry[0], 'role': entry[1], 'time': now})
                    syslog.syslog('oncall active ' + event['summary'])
    return oncall


def on_message(client, userdata, message):
    contacts = userdata['contacts']
    primary_name = get_on_call_person('primary')
    primary_contact = contacts.get(primary_name)
    email = primary_contact.get('email') if primary_contact else None
    decoded_message = json.loads(message.payload)
    alert_message = decoded_message.get('MsgText')
    alert_time = decoded_message.get('TimeString')
    if decoded_message.get('StateAfter') == '0':
        alert_message = 'Cleared: ' + alert_message
    else:
        alert_message = 'Active: ' + alert_message

    syslog.syslog('mqtt message: ' + message.payload.decode('utf-8'))
    try:
        alert_time_data = datetime.datetime.strptime(alert_time, '%d/%m/%Y %H:%M:%S')
    except ValueError:
        alert_time_string = alert_time
        alert_age = datetime.timedelta(seconds=1)
        alert_time_data = datetime.datetime.now(datetime.UTC)
    else:
        alert_time_string = alert_time_data.strftime('%Y-%m-%dT%H:%M:%S')
        compare_now = datetime.datetime.strptime(
            datetime.datetime.now(datetime.UTC).strftime('%d/%m/%Y %H:%M:%S'),
            '%d/%m/%Y %H:%M:%S',
        )
        alert_age = compare_now - alert_time_data

    if alert_age < IGNORE_ALERTS_OLDER_THAN:
        log_alert_message(alert_time_string, alert_message)
        if not check_dup(alert_message):
            token = generate_token(email, alert_message, ALERT_ESCALATION_TIME)
            sendntfy(alert_message, alert_time_data, token)
    elif not check_dup('Ignoring old alerts'):
        token = generate_token(email, 'Ignoring old alerts', ALERT_ESCALATION_TIME)
        sendntfy('Ignoring old alerts', datetime.datetime.now(datetime.UTC), token)
        check_token(token)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(MQTT_TOPIC, MQTT_QOS)
        syslog.syslog('Connected and subscribed to ' + MQTT_TOPIC)
    else:
        syslog.syslog('Connection fail')


def on_log(client, userdata, level, message):
    return


def get_secret(secret_key):
    secret_name = 'RdgHydroServerSecrets'
    region_name = 'eu-west-2'
    session = boto3.session.Session()
    secrets_client = session.client(service_name='secretsmanager', region_name=region_name)
    response = secrets_client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString']).get(secret_key)


def _load_contacts():
    with open('/etc/hydro/oncall-contacts.cfg', 'r', encoding='utf-8') as contacts_file:
        return json.load(contacts_file)


def _contact_email(contacts, role):
    contact = contacts.get(get_on_call_person(role))
    return contact.get('email') if contact else None


def run_worker():
    contacts = _load_contacts()
    timezone = pytz.timezone('Europe/London')
    now = datetime.datetime.now(timezone)
    now_string = now.strftime('%Y-%m-%dT%H:%M:%S')
    sendntfy('Alert Service Startup', datetime.datetime.now(datetime.UTC), '')
    log_alert_message(now_string, 'Alert Service startup')

    last_hour = -1
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
        client_id='purple',
    )
    client.user_data_set({'contacts': contacts})
    client.username_pw_set('mqttrota', get_secret('MQTT_ROTA_PWD'))
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_log = on_log
    client.tls_set('/etc/ssl/certs/ca-certificates.crt')

    latest_data_time = datetime.datetime.now(datetime.UTC)
    next_data_report_time = latest_data_time
    no_data_alert_active = False
    google_api_key = get_secret('GOOGLE_API_KEY')
    google_calendar_id = get_secret('CALENDAR_ID')

    try:
        client.connect(MQTT_BROKER, MQTT_BROKER_PORT)
        syslog.syslog('connecting to mqtt broker ' + MQTT_BROKER)
        client.loop_start()
    except Exception:
        syslog.syslog('mqtt broker connection failed')
        log_alert_message(now_string, 'mqtt broker connection failed')

    try:
        while True:
            alert_messages = []
            now_utc = datetime.datetime.now(datetime.UTC)
            now = datetime.datetime.now(timezone)
            now_string = now.strftime('%Y-%m-%dT%H:%M:%S')

            if last_hour != now.hour:
                last_hour = now.hour
                new_who_is_oncall = calendar_read(google_api_key, google_calendar_id, contacts)
                for role in ('primary', 'second'):
                    for person in new_who_is_oncall:
                        if person['role'] == role:
                            previous_name = update_on_call_person(role, person.get('name'))
                            if person.get('name') != previous_name:
                                message = 'On-Call for {role} is now {name}'.format(
                                    role=role, name=person.get('name'))
                                sendntfy(message, now, '')
                                log_alert_message(now_string, message)
                    if last_hour == 7:
                        email = _contact_email(contacts, role)
                        message = 'Sending oncall reminder to ' + str(get_on_call_person(role)) + ' for role ' + role
                        token = generate_token(email, message, ONCALL_ESCALATION_TIME)
                        sendntfy(message, now, token)
                        token_mark_sent(token)
                        log_alert_message(now_string, message)

            email = _contact_email(contacts, 'primary')
            tokenlist = expired_token()
            for entry in tokenlist:
                if entry.get('count') == 0:
                    message = 'Escalate: ' + entry.get('message')
                    sendntfy(message, now, '')
                else:
                    alert_message = 'Repeated: {count:d} message: {message}'.format(
                        count=entry.get('count'), message=entry.get('message'))
                    token = generate_token(email, alert_message, ALERT_ESCALATION_TIME)
                    alert_messages.append(alert_message)
                    sendntfy(alert_message, now, token)
                    log_alert_message(now_string, alert_message)

            for entry in active_token():
                if not entry.get('sent'):
                    alert_messages.append(entry.get('message'))
                    token_mark_sent(entry.get('token'))

            try:
                latest_request = request.urlopen('https://readinghydro.org/api/plc/current', timeout=6)
            except (HTTPError, URLError, TimeoutError) as error:
                syslog.syslog('Data not retrieved because of {error}'.format(error=error))
            else:
                with latest_request:
                    latest_data = json.loads(latest_request.read())
                latest_data_time = datetime.datetime.strptime(
                    latest_data.get('received_at'), '%Y-%m-%dT%H:%M:%SZ')
                latest_data_time = latest_data_time.replace(tzinfo=datetime.timezone.utc)

            if latest_data_time < now_utc - NO_DATA_REPORT_EVENT:
                if now_utc > next_data_report_time:
                    next_data_report_time = now_utc + NO_DATA_RE_REPORT_TIME
                    no_data_alert_active = True
                    alert_message = 'Active: No data received since ' + latest_data_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                    alert_message += ' That is {minutes:5.2f} Minutes ago'.format(
                        minutes=(now_utc - latest_data_time).seconds / 60)
                    token = generate_token(
                        email,
                        'At: {time} message: {message}'.format(time=now_string, message=alert_message),
                        datetime.timedelta(minutes=15),
                    )
                    alert_messages.append(alert_message)
                    sendntfy(alert_message, now, token)
                    log_alert_message(now_string, alert_message)
            else:
                if no_data_alert_active:
                    alert_message = 'Cleared: Data feed has resumed at ' + latest_data_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                    token = generate_token(
                        email,
                        'At: {time} message: {message}'.format(time=now_string, message=alert_message),
                        datetime.timedelta(minutes=15),
                    )
                    alert_messages.append(alert_message)
                    sendntfy(alert_message, now, token)
                    log_alert_message(now_string, alert_message)
                no_data_alert_active = False

            time.sleep(30)
    finally:
        client.loop_stop()
        log_alert_message(now_string, 'Alert Service shutdown')
