#! /usr/bin/python3
import json
import paho.mqtt.client as mqtt
import time, datetime
import threading
from calendarread import calendarread
from restServer import restServer
from tokenHandeler import generate_token, expired_token
from sendmail import sendMail_alert, sendMail_shift, sendMail_esclate
from urllib import request

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


def on_message(client, userdata, message):
    decoded_message = json.loads(message.payload)
    email1 = contacts.get(who_is_oncall.get('primary')).get('email')
    email2 = contacts.get(who_is_oncall.get('second')).get('email')
    alertMessage = decoded_message.get('MsgText')
    alertTime = decoded_message.get('TimeString')
    token = generate_token(email1, 'At: {time} message: {message}'.format(time=alertTime, message=alertMessage), datetime.timedelta(seconds=5*60))
    sendMail_alert(email1,alertMessage,alertTime, token)
    sendMail_alert(email2,alertMessage,alertTime, token)

def on_connect(client, userdata, flags, rc):
    if rc==0:
        client.subscribe(topic,qos)
        print("Connected and subscribed to ",topic)

    else:
        print("Connection fail")

def on_log(client, userdata, level, buf):
    print("log: ",buf)



# Use this code snippet in your app.
# If you need more information about configurations or implementing the sample code, visit the AWS docs:  
# https://aws.amazon.com/developers/getting-started/python/

import boto3
import base64
from botocore.exceptions import ClientError


def get_secret(MySecretString):

    secret_name = "RdgHydroServerSecrets"
    region_name = "eu-west-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager',region_name=region_name)

    get_secret_value_response = client.get_secret_value(SecretId=secret_name)

    all_secret = json.loads(get_secret_value_response['SecretString'])
    secret = all_secret.get(MySecretString)
    return secret

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

next_data_report_time = datetime.datetime.now()

google_api_key = get_secret('GOOGLE_API_KEY')

try:
    client.connect(mqtt_broker, mqtt_broker_port)
    print("connecting to broker", mqtt_broker)
    client.loop_start()

except:
    print("connection failed")

# Start the restServer in another thread
print('Starting the REST Server')
restThread = threading.Thread(target=restServer, daemon=True)
restThread.start()

# read the calendar once an hour, if there is an entry for each of the roles update the current role person
# if there is no new entry for a role the old entry will be kept

try:
    while True:
        now_utc = datetime.datetime.utcnow()
        now = datetime.datetime.now()
        now_utc_string = now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        now_string = now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        if last_hour != now.hour:
            last_hour = now.hour
            new_who_is_oncall = calendarread(google_api_key)
            for role in ('primary', 'second'):
                for person in new_who_is_oncall:
                    if person['role'] == role:
                        who_is_oncall.update({role: person.get('name')})
                if last_hour == 9:
                    email = contacts.get(who_is_oncall.get(role)).get('email')
                    message='Sending oncall reminder to '+ who_is_oncall.get(role)+ ' at '+email+' for role '+role
                    sendMail_shift(email, role, generate_token(email, message, datetime.timedelta(seconds=15*60)))

# look through the alert list for any expited alerts that have not been acknowleged.
        tokenlist = expired_token()
        for entry in tokenlist:
            token = generate_token('alerts@readinghydro.org','Esculate: '+entry.get('message'), datetime.timedelta(seconds=5*60))
            sendMail_esclate('alerts@readinghydro.org', 'Esculate: '+entry.get('message'), token)

# check the data feeds to see if we have current data, if not raise an alert
        latest_request = request.urlopen('https://readinghydro.org:9445/api/plc/current')
        latest_data = json.loads(latest_request.read())
        latest_data_time = datetime.datetime.strptime(latest_data.get('received_at'), '%Y-%m-%dT%H:%M:%S.%fZ')
        print('That is {minutes:.2} Minutes ago'.format(minutes=(now_utc-latest_data_time).seconds/60), next_data_report_time)
        if latest_data_time < now_utc - datetime.timedelta(seconds=20*60):
            if now > next_data_report_time:
                next_data_report_time = now + datetime.timedelta(seconds=15*60)
                email1 = contacts.get(who_is_oncall.get('primary')).get('email')
                email2 = contacts.get(who_is_oncall.get('second')).get('email')
                alertMessage = 'No data recieved since '+latest_data_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                alertMessage += ' That is {minutes:.2} Minutes ago'.format(minutes=(now_utc-latest_data_time).seconds/60)
                token = generate_token(email1, 'At: {time} message: {message}'.format(time=now_string, message=alertMessage), datetime.timedelta(seconds=5*60))
                sendMail_alert(email1,alertMessage,now_string, token)
                sendMail_alert(email2,alertMessage,now_string, token)



        time.sleep(30)
        pass

except KeyboardInterrupt:
    print("interrrupted by keyboard")

client.loop_stop() #stop loop
time.sleep(5)
