#! /usr/bin/python3


import paho.mqtt.client as mqtt
import time


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
topic = "#"
qos=0

client = mqtt.Client("purple")

client.username_pw_set("stuart","ecl1ps3")
client.on_connect = on_connect
client.on_message = on_message
client.on_log = on_log
client.tls_set("/etc/ssl/certs/ca-certificates.crt")

try:
    client.connect(mqtt_broker,mqtt_broker_port)
    print("connecting to broker",mqtt_broker)
    client.loop_start()

except:
    print("connection failed")

try:
    while True:
        time.sleep(1)
        pass

except KeyboardInterrupt:
    print("interrrupted by keyboard")

client.loop_stop() #stop loop
topic_watcher_flag=False #stop logging thread
time.sleep(5)
