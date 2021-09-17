#! /usr/bin/python3

import os
 
def sendMail_alert(to_addr, alert, time, token):
 
    text = '''\
From: turbine.house@readinghydro.org
To: {to_addr}
Subject: Hydro ALERT: {alert}
Hello this is an automated alert from the Reading Hydro turbine room:
Alert received at: {time}
Alert Message: {alert}
Please confirm reciept of this alert <a href="http://readinghydro.org:8080/ackresp?token={token}">by clicking here</a>.
'''

    msg = text.format(to_addr=to_addr, alert=alert, time=time, token=token)
    
    command = 'echo "{msg}" | /use/sbin/sendmail {to_addr}'.format(msg=msg, to_addr=to_addr)
    try:
        os.system(command)
    except:
        print('Failed to send email')

def sendMail_shift(to_addr, token):
 
    text = '''\
From: turbine.house@readinghydro.org
To: {to_addr}
Subject: Hydro On-Call Shift 
Hello this is an automated message from the Reading Hydro turbine room:
You are sheduled as On-Call for today
Please confirm reciept of this notice <a href="http://readinghydro.org:8080/ackresp?token={token}">by clicking here</a>.
'''

    msg = text.format(to_addr=to_addr, token=token)
    
    command = 'echo "{msg}" | /use/sbin/sendmail {to_addr}'.format(msg=msg, to_addr=to_addr)
    try:
        os.system(command)
    except:
        print('Failed to send email')

def sendMail_esclate(to_addr, token):
 
    text = '''\
From: turbine.house@readinghydro.org
To: {to_addr}
Subject: Hydro ALERT ESCALATION
Hello this is an automated message from the Reading Hydro turbine room:
The alert has not been acknowleged
Please confirm reciept of this notice <a href="http://readinghydro.org:8080/ackresp?token={token}">by clicking here</a>.
'''

    msg = text.format(to_addr=to_addr, token=token)
    
    command = 'echo "{msg}" | /use/sbin/sendmail {to_addr}'.format(msg=msg, to_addr=to_addr)
    try:
        os.system(command)
    except:
        print('Failed to send email')

# Example:
#import datetime

#sendMail_alert('stuart.ward.uk@gmail.com','test alert', datetime.datetime.now(), 'ABCD1234')
#sendMail_shift('stuart.ward.uk@gmail.com', 'EFGH1234')
#sendMail_esclate('stuart.ward.uk@gmail.com', 'JKLM1234')
