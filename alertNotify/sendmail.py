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
Please confirm receipt of this alert https://readinghydro.org/ackresp?token={token}
You can see all the active alert messages here: https://readinghydro.org/alertlist
'''

    msg = text.format(to_addr=to_addr, alert=alert, time=time, token=token)
    
    command = 'echo "{msg}" | /usr/sbin/sendmail {to_addr}'.format(msg=msg, to_addr=to_addr)
    os.system(command)

def sendMail_shift(to_addr, role, token):
 
    text = '''\
From: turbine.house@readinghydro.org
To: {to_addr}
Subject: Hydro On-Call Shift 
Hello this is an automated message from the Reading Hydro turbine room:
You are sheduled as {role} On-Call for today
Please confirm receipt of this notice https://readinghydro.org/ackresp?token={token}
Current on-call roles are listed here: https://readinghydro.org/whoisoncall
You can see all the alert messages here: https://readinghydro.org/alertlist
'''

    msg = text.format(to_addr=to_addr, role=role, token=token)
    
    command = 'echo "{msg}" | /usr/sbin/sendmail {to_addr}'.format(msg=msg, to_addr=to_addr)
    os.system(command)

def sendMail_escalate(to_addr, message):
 
    text = '''\
From: turbine.house@readinghydro.org
To: {to_addr}
Subject: Hydro ALERT ESCALATION
Hello this is an automated message from the Reading Hydro turbine room:
{message}
The alert has not been acknowledged
Current on-call roles are listed here: https://readinghydro.org/whoisoncall
You can see all the alert messages here: https://readinghydro.org/alertlist
'''

    msg = text.format(to_addr=to_addr, message=message)
    
    command = 'echo "{msg}" | /usr/sbin/sendmail {to_addr}'.format(msg=msg, to_addr=to_addr)
    os.system(command)

if __name__ == '__main__':
# Example:
    import datetime

    sendMail_alert('stuart.ward.uk@gmail.com','test alert', datetime.datetime.now(), 'ABCD1234')
    sendMail_shift('stuart.ward.uk@gmail.com', 'primary', 'EFGH1234')
    sendMail_escalate('stuart.ward.uk@gmail.com', 'Orignal message is here')
