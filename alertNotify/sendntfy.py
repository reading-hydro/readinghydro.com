#! /usr/bin/python3

import datetime
import requests
from requests.exceptions import HTTPError

def sendntfy(alert: str, time: datetime, token: str):
    head4 = "view, Acknowledge, https://readinghydro.org/ackresp?token=" 
    head4 = head4 + token
    url = "https://ntfy.sh/alerts-readinghydro-org"
    head1 = "Reading Hydro Alert"
    data = time.strftime("%Y-%m-%dT%H:%M:%SZ") + " " + alert
    if alert[0] == "A" or alert[0] == "E":
        head2 = "urgent"
        head3 = "droplet,warning"
    else:
        head2 = "low"
        head3 = "droplet"
    
    try:
        if len(token) > 2:
            responce = requests.put(url=url, data=data, headers={"Title": head1, "Priority": head2, "Tags": head3, "Actions": head4})
        else:
            responce = requests.put(url=url, data=data, headers={"Title": head1, "Priority": head2, "Tags": head3})
        print(responce)
    except HTTPError as http_err:
        print("http put error", http_err)
    else:
        print("sent", responce.content)
    

if __name__ == '__main__':
    sendntfy("Active: Test alert message", datetime.datetime.now(datetime.UTC),
             "igUwV-l3fgId1sU_Dvgk2Eo8-ZTKUNARAfz4QeSagpw=")
    sendntfy("Cleared: test alert message", datetime.datetime.now(datetime.UTC),
             "igUwV-l3fgId1sU_Dvgk2Eo8-ZTKUNARAfz4QeSagpw=")
    sendntfy("Escalate: Test Alert Message", datetime.datetime.now(datetime.UTC), "")
    sendntfy("Repeated: Test Alert Message", datetime.datetime.now(datetime.UTC), "")
