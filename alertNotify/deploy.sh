#!/bin/bash
# Deploy script for readinghydro.com alert notification system
set -e
echo "stop the existing alertNotify service"
sudo systemctl stop hydro-alert-notify.service
echo "copy files to /usr/local/bin/alertNotify"
if [ ! -d /usr/local/bin/alertNotify ]; then
    echo "creating /usr/local/bin/alertNotify directory"
    sudo mkdir -p /usr/local/bin/alertNotify
fi
sudo cp alert_service.py /usr/local/bin/alertNotify/alert_service.py
sudo cp tokenHandeler.py /usr/local/bin/alertNotify/tokenHandeler.py
sudo cp sendntfy.py /usr/local/bin/alertNotify/sendntfy.py
echo "start the alertNotify service"
sudo systemctl start hydro-alert-notify.service
sudo systemctl status hydro-alert-notify.service --no-pager -l
echo "deployment complete"
