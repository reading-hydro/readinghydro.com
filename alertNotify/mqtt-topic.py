#! /usr/bin/python3

import paho.mqtt.client as mqtt
import time, datetime, threading
from calendarread import calendarread
from restServer import restServer


def on_message(client, userdata, message):
    print("message received " ,str(message.payload.decode("utf-8")))
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain)


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
topic = "hydro-data"
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
try:
    print('Starting the REST Server')
    threading.Thread(target=restServer).start()
except:
    print('Failed to start the REST server')

# read the calendar once an hour, if there is an entry for each of the roles update the current role person
# if there is no new entry for a role the old entry will be kept

try:
    while True:
        if lastHour != datetime.datetime.hour :
            lastHour = datetime.datetime.hour
            new_who_is_oncall = calendarread()
            for role in ('primary', 'second'):
                for person in new_who_is_oncall:
                    if person['role'] == role:
                        who_is_oncall.update({role: person.get('name')})
 
        time.sleep(10)
        pass

except KeyboardInterrupt:
    print("interrrupted by keyboard")

client.loop_stop() #stop loop
topic_watcher_flag=False #stop logging thread
time.sleep(5)
