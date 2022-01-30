#! /usr/bin/python3

import cgi
from calendarread import calendarread
from tokenHandeler import generate_token, check_token, active_token


def notfound_404(environ, start_response):
    start_response('404 Not Found', [('Content-type', 'text/plain')])
    return [b'Not Found']


class PathDispatcher:
    def __init__(self):
        self.pathmap = {}

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO']
        params = cgi.FieldStorage(environ['wsgi.input'], environ=environ)
        method = environ['REQUEST_METHOD'].lower()
        environ['params'] = {key: params.getvalue(key) for key in params}
        handler = self.pathmap.get((method, path), notfound_404)
        return handler(environ, start_response)

    def register(self, method, path, function):
        self.pathmap[method.lower(), path] = function
        return function


_oncall_resp = '''\
<html>
  <head>
     <title>Reading Hydro On-Call</title>
   </head>
   <body>
     <h1>Current on call Primary contact is {name1}</h1>
     <h1>Current on call Secondary contact is {name2}</h1>
   </body>
</html>'''


who_is_oncall = {'primary': '', 'second': ''}


def whoisoncall(environ, start_response):
    start_response('200 OK', [('Content-type', 'text/html')])
    new_who_is_oncall = calendarread()
    for role in ('primary', 'second'):
        for person in new_who_is_oncall:
            if person['role'] == role:
                who_is_oncall.update({role: person.get('name')})
    resp = _oncall_resp.format(name1=who_is_oncall.get('primary'), name2=who_is_oncall.get('second'))
    yield resp.encode('utf-8')


_ack_resp_ok = '''\
<html>
  <head>
     <title>Reading Hydro On-Call</title>
   </head>
   <body>
     <h1>Acknowlegement of alert Sucessful</h1>
   </body>
</html>'''


_ack_resp_fail = '''\
<html>
  <head>
     <title>Reading Hydro On-Call</title>
   </head>
   <body>
     <h1>Acknowlegement of alert Failed</h1>
   </body>
</html>'''


def ackresp(environ, start_response):
    start_response('200 OK', [('Content-type', 'text/html')])
    params = environ['params']
    token = params.get('token')
    if check_token(token):
        resp = _ack_resp_ok
    else:
        resp = _ack_resp_fail
    yield resp.encode('utf-8')


_ack_list_head = '''\
<html>
  <head>
     <title>Reading Hydro On-Call</title>
   </head>
   <body>
     <h1>Acknowlegement alerts currently active</h1>
     <table><tr><th>Token</th><th>Email address</th><th>Expiary Time</th><th>Status</th><th>Message</th></tr>'''


_ack_list_body = '''\
    <tr><td><a href="http://readinghydro.org:8080/ackresp?token={token}">Token</a></td><td>{email}</td>
    <td>{time}</td><td>{status}</td><td>{message}</td></tr>
    '''


_ack_list_tail = '''\
    </table>
   </body>
</html>'''


def alertlist(environ, start_response):
    start_response('200 OK', [('Content-type', 'text/html')])
    tokenlist = active_token()
    resp = _ack_list_head
    for entry in tokenlist:
        status = 'live'
        if entry.get('ack'):
            status = 'Acknowleged'
        resp = resp + _ack_list_body.format(token=entry.get('token'), email=entry.get('email'),
                                            time=entry.get('time'), status=status, message=entry.get('message'))
    resp = resp + _ack_list_tail
    yield resp.encode('utf-8')


def restServer():
    from wsgiref.simple_server import make_server

    # Create the dispatcher and register functions
    dispatcher = PathDispatcher()
#   dispatcher.register('GET', '/whoisoncall', whoisoncall)
    dispatcher.register('GET', '/ackresp', ackresp)
    dispatcher.register('GET', '/alertlist', alertlist)

    # Launch a basic server
    httpd = make_server('', 8080, dispatcher)
    print('Serving on port 8080...')
    httpd.serve_forever()
