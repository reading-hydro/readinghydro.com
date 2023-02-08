#! /usr/bin/python3
# This generated and saves tokens that are used to confirm message reciept Tokens are active for 5 minutes
# and are acknowleged with the check_token call. expired_token is called at regular intivals to indicate any
# tokens that have not been acknowleged, and these are removed.
# check new messages for duplicates with the check_dup if found the message should not be sent and a message
# of the number of duplicates sent when expiring the message.

import hashlib
import base64
import datetime

token_table = []


def generate_token(emailAddr: str, message: str, lifetime: datetime) -> str:
    timekey = datetime.datetime.now() + lifetime
    hash = hashlib.sha256()
    hash.update(bytes(emailAddr, "ascii"))
    hash.update(bytes(timekey.isoformat(), "ascii"))
    hash.update(b'Readinghydro token service')
    token = (base64.urlsafe_b64encode(hash.digest())).decode()
    token_table.append({'token': token, 'email': emailAddr, 'time': timekey,
                 'ack': False, 'message': message, 'count': 0, 'sent': False})
    return token


def check_dup(message: str) -> bool:
    for entry in token_table:
        if entry.get('message') == message:
            count = entry.get('count')
            entry.update({'count': count+1})
            return True
    return False


def check_token(token: str) -> bool:
    token_state = False
    token_email = ''
    for entry in token_table:
        if entry.get('token') == token:
            if entry.get('time') > datetime.datetime.now():
                entry.update({'ack': True})
                token_email = entry.get('email')
                token_state = True
    if token_state:
        for entry in token_table:
            if entry.get('email') == token_email:
                entry.update({'ack': True})
    return token_state

def token_mark_sent(token: str):
    for entry in token_table:
        if entry.get('token') == token:
            entry.update({'sent': True})
    return

def active_token() -> list:
    tokens = []
    for entry in token_table:
        if entry.get('time') > datetime.datetime.now():
            tokens.append(entry)
    return tokens


def expired_token() -> list:
    tokens = []
    for entry in token_table:
        if entry.get('time') < datetime.datetime.now():
            if entry.get('ack'):
                if entry.get('count') > 0:
                    tokens.append(entry)
                token_table.remove(entry)
            else:
                tokens.append(entry)
                token_table.remove(entry)
    return tokens


def main():
    import time
    t = generate_token('stuart.ward.uk@gmail.com', 'message 1 contents', datetime.timedelta(seconds=5*60))
    t = generate_token('stuart.ward.uk@gmail.com', 'message 2 contents', datetime.timedelta(seconds=5*60))
    t = generate_token('stuart.ward.uk@gmail.com', 'message 3 contents', datetime.timedelta(seconds=5*60))
    print(token_table)
    if check_dup('message 1 contents'):
        print('Duplicate found')
    time.sleep(5)
    print(active_token())
    print(check_token(t))
    token_mark_sent(t)
    print(token_table)
    return


if __name__ == '__main__':
    main()
