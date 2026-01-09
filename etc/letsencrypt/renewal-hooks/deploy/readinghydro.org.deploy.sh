#! /bin/bash
# Script to restart services after Let's Encrypt certificate renewal
#
# copy the certifacte files for the mosquitto broker
cp -L /etc/letsencrypt/live/readinghydro.org/cert.pem /etc/mosquitto/certs/cert.pem
cp -L /etc/letsencrypt/live/readinghydro.org/privkey.pem /etc/mosquitto/certs/privkey.pem
cp -L /etc/letsencrypt/live/readinghydro.org/chain.pem /etc/mosquitto/certs/chain.pem
chown mosquitto:mosquitto /etc/mosquitto/certs/cert.pem
chown mosquitto:mosquitto /etc/mosquitto/certs/privkey.pem
chown mosquitto:mosquitto /etc/mosquitto/certs/chain.pem
chmod 640 /etc/mosquitto/certs/cert.pem
chmod 640 /etc/mosquitto/certs/privkey.pem
chmod 640 /etc/mosquitto/certs/chain.pem
# restart services to pick up the new certificates
systemctl restart hydro-api.service
systemctl restart mosquitto.service
systemctl restart apache2.service

