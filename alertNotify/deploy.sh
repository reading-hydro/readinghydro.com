#!/bin/bash
# Deploy script for readinghydro.com alert notification system
set -e
echo "stoping the existing alertNotify service"
sudo systemctl stop hydro-alert-notify.service
sleep 2
echo "copy files to /usr/local/bin/alertNotify"
if [ ! -d /usr/local/bin/alertNotify ]; then
    echo "creating /usr/local/bin/alertNotify directory"
    sudo mkdir -p /usr/local/bin/alertNotify
fi
sudo cp alert_service.py /usr/local/bin/alertNotify/alert_service.py
sudo cp alert_web.py /usr/local/bin/alertNotify/alert_web.py
sudo cp alert_worker.py /usr/local/bin/alertNotify/alert_worker.py
sudo cp shared_state.py /usr/local/bin/alertNotify/shared_state.py
sudo cp tokenHandeler.py /usr/local/bin/alertNotify/tokenHandeler.py
sudo cp sendntfy.py /usr/local/bin/alertNotify/sendntfy.py
echo "start the alertNotify service"
sudo systemctl start hydro-alert-notify.service
sleep 2
sudo systemctl status hydro-alert-notify.service --no-pager -l
echo "deployment complete"
