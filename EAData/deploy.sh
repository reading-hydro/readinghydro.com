#! /bin/bash

sudo cp EADataCollector.py /usr/local/bin/EADataCollector.py
sudo cp eadatacron /etc/cron.hourly/eadatacron
sudo chmod +x /usr/local/bin/EADataCollector.py
sudo chmod +x /etc/cron.hourly/eadatacron

