import datetime
from html import escape
from urllib.parse import parse_qs

from shared_state import get_alert_log_snapshot, get_on_call_snapshot
from tokenHandeler import active_token, check_token


_ACK_RESP_OK = '''\
<html>
  <head>
     <title>Reading Hydro Alert Acknowledgement</title>
     <meta http-equiv="refresh" content="600">
   </head>
   <body>
     <h1>Acknowledgement of alert Sucessful</h1>
     <h1>Acknowledgement alerts currently active</h1>
     <table><tr><th>Token</th><th>Expiary Time</th><th>Status</th><th>Count</th><th>Message</th></tr>
     '''

_ACK_RESP_FAIL = '''\
<html>
  <head>
     <title>Reading Hydro Alert Acknowledgement</title>
     <meta http-equiv="refresh" content="600">
   </head>
   <body>
     <h1>Acknowledgement of alert Failed</h1>
     <h1>Acknowledgement alerts currently active</h1>
     <table><tr><th>Token</th><th>Expiary Time</th><th>Status</th><th>Count</th><th>Message</th></tr>
     '''

_ACK_LIST_TAIL = '''\
    </table>
   </body>
</html>'''

_ALERT_LIST_HEAD = '''\
<html>
  <head>
     <title>Reading Hydro Alert Activity</title>
     <meta http-equiv="refresh" content="600">
   </head>
   <body>
     <h1>Alert history at {time}</h1>
     <table><tr><th>Time</th><th>Message</th></tr>
     '''

_ALERT_LIST_TAIL = '''\
    </table>
   </body>
</html>'''


def _text(value):
    return escape(str(value))


def _whoisoncall():
    on_call = get_on_call_snapshot()
    return '''\
<html>
  <head>
     <title>Reading Hydro On-Call</title>
   </head>
   <body>
     <h1>Current on call Primary contact is {primary}</h1>
     <h1>Current on call Secondary contact is {second}</h1>
   </body>
</html>'''.format(primary=_text(on_call.get('primary')), second=_text(on_call.get('second')))


def _ackresp(token):
    response = _ACK_RESP_OK if check_token(token) else _ACK_RESP_FAIL
    for entry in active_token():
        status = 'Acknowledged' if entry.get('ack') else 'Live'
        response += '''\
    <tr><td><a href="https://readinghydro.org/ackresp?token={token}">Token</a></td>
    <td>{time}</td><td>{status}</td><td>{count}</td><td>{message}</td></tr>
    '''.format(token=_text(entry.get('token')), time=_text(entry.get('time')),
               status=status, count=_text(entry.get('count')),
               message=_text(entry.get('message')))
    return response + _ACK_LIST_TAIL


def _alertlist():
    now = datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
    response = _ALERT_LIST_HEAD.format(time=_text(now))
    for entry in get_alert_log_snapshot():
        response += '''\
    <tr><td>{time} </td><td>{message}</td></tr>
    '''.format(time=_text(entry.get('time')), message=_text(entry.get('message')))
    return response + _ALERT_LIST_TAIL


async def app(scope, receive, send):
    if scope['type'] != 'http':
        return

    status = 200
    if scope['method'] != 'GET':
        status = 405
        body = 'Method Not Allowed'
        content_type = 'text/plain; charset=utf-8'
    else:
        path = scope['path']
        if path == '/whoisoncall':
            body = _whoisoncall()
        elif path == '/ackresp':
            query = parse_qs(scope['query_string'].decode('ascii', errors='replace'),
                             keep_blank_values=True)
            body = _ackresp(query.get('token', [None])[0])
        elif path == '/alertlist':
            body = _alertlist()
        else:
            status = 404
            body = 'Not Found'
            content_type = 'text/plain; charset=utf-8'
        if status == 200:
            content_type = 'text/html; charset=utf-8'

    encoded_body = body.encode('utf-8')
    await send({
        'type': 'http.response.start',
        'status': status,
        'headers': [
            (b'content-type', content_type.encode('ascii')),
            (b'content-length', str(len(encoded_body)).encode('ascii')),
        ],
    })
    await send({'type': 'http.response.body', 'body': encoded_body})
