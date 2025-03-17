#! /usr/bin/python3

import sys
import datetime
from paho.mqtt import client as mqtt

def connect_mqtt():
    mqttClient = mqtt.Client('upsmon')
    mqttClient.username_pw_set('upsmon', 'upsmon')
    mqttClient.connect('readinghydro.org', 1883)
    return mqttClient

def publish_mqtt(mqttClient, message):
    mqttClient.publish('hydro-alert', message)
    mqttClient.disconnect()

if len(sys.argv) < 2:
    print("Usage: ups_send_alert.py <message>")
    sys.exit(1)

message = sys.argv[1]
print("Sending message:", message)

mqttClient = connect_mqtt()
mqttClient.loop_start()
publish_mqtt(mqttClient, message)
mqttClient.loop_stop()
mqttClient.disconnect()

