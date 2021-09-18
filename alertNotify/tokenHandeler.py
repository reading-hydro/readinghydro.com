#! /usr/bin/python3
# This generated and saves tokens that are used to confirm message reciept Tokens are active for 5 minutes
# and are acknowleged with the check_token call. expired_token is called at regular intivals to indicate any 
# tokens that have not been acknowleged, and these are removed.

import hashlib, base64, datetime

token_table = []


def generate_token(emailAddr, message):
    timekey = datetime.datetime.now()
    hash = hashlib.sha256()
    hash.update(bytes(emailAddr,"ascii"))
    hash.update(bytes(timekey.isoformat(),"ascii"))
    hash.update(b'Readinghydro token service')
    token = (base64.urlsafe_b64encode(hash.digest())).decode()
    token_table.append({'token': token, 'email': emailAddr, 'time': timekey, 'ack': False, 'message': message})
    return token

def check_token(token):
    timekey = datetime.datetime.now()
    for entry in token_table:
        if entry.get('token') == token:
            if (((timekey - entry.get('time')).seconds) < 5*60):
                entry.update({'ack': True})
                return True
    return False        

def active_token():
    timekey = datetime.datetime.now()
    tokens = []
    for entry in token_table:
        if (((timekey - entry.get('time')).seconds) < 5*60):
            tokens.append(entry)
    return tokens

def expired_token():
    timekey = datetime.datetime.now()
    tokens = []
    for entry in token_table:
        if (((timekey - entry.get('time')).seconds) >= 5*60):
            if entry.get('ack'):
                token_table.remove(entry)
            else:
                tokens.append(entry)
                token_table.remove(entry)
    return tokens

#import time
#t = generate_token('stuart.ward.uk@gmail.com','message contents')
#print(token_table)
#time.sleep(5)
#print(active_token())
#print(check_token(t))
#print(token_table)
