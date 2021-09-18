#! /usr/bin/python3
import json
import paho.mqtt.client as mqtt
import time, datetime, threading, cgi
from calendarread import calendarread
from restServer import restServer
from tokenHandeler import generate_token, expired_token
from sendmail import sendMail_alert, sendMail_shift, sendMail_esclate

# Contacts hard coded for the moment need to add this in a database.

contacts = {
    'stuart':{'email': 'stuart.ward.uk@gmail.com'},
    'austin':{'email': 'austindangerjacobs@gmail.com'},
    'jo':{'email': 'jo.ramsay@gmail.com'},
    'rupert':{'email': 'info@rupes.net'},
    'tim':{'email': 'tim@milkreading.co.uk'},
    'sophie':{'email':'sophie@fenwickpaul.com'},
    'daniel':{'email': 'daniel.cameron@sky.com'}
    }


def on_message(client, userdata, message):
    print("message received " ,str(message.payload.decode("utf-8")))
    print("message topic=",message.topic)
    decodedMessage = json.loads(message.payload)
    email1 = contacts.get(who_is_oncall.get('primary')).get('email')
    email2 = contacts.get(who_is_oncall.get('second')).get('email')
    alertMessage = decodedMessage.get('MsgText')
    alertTime = decodedMessage.get('TimeString')
    token = generate_token(email1,'At: {time} message: {message}'.format(time=alertTime, message=alertMessage))
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



mqtt_broker = 'readinghydro.org'
mqtt_broker_port = 8883
topic = "hydro-alert"
qos=0
lastHour = -1

client = mqtt.Client("purple")

client.username_pw_set("mqttrota","R0t@vaTOR")
client.on_connect = on_connect
client.on_message = on_message
client.on_log = on_log
client.tls_set("/etc/ssl/certs/ca-certificates.crt")
who_is_oncall = {'primary' : '', 'second': ''}

try:
    client.connect(mqtt_broker,mqtt_broker_port)
    print("connecting to broker",mqtt_broker)
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
        if lastHour != datetime.datetime.now().hour:
            lastHour = datetime.datetime.now().hour
            new_who_is_oncall = calendarread()
            for role in ('primary', 'second'):
                for person in new_who_is_oncall:
                    if person['role'] == role:
                        who_is_oncall.update({role: person.get('name')})
                if lastHour == 9:
                    email = contacts.get(who_is_oncall.get(role)).get('email')
                    message='Sending oncall reminder to '+ who_is_oncall.get(role)+ ' at '+email+' for role '+role
                    sendMail_shift(email, role, generate_token(email,message))

# look through the alert list for any expited alerts that have not been acknowleged.
        tokenlist = expired_token()
        for entry in tokenlist:
            token = generate_token('alerts@readinghydro.org','Esculate: '+entry.get('message'))
            sendMail_esclate('alerts@readinghydro.org', 'Esculate: '+entry.get('message'), token)

        time.sleep(1)
        pass

except KeyboardInterrupt:
    print("interrrupted by keyboard")

client.loop_stop() #stop loop
time.sleep(5)
