#! /bin/bash
systemctl restart hydro-api.service
systemctl restart mosquitto.service
systemctl restart apache2.service

