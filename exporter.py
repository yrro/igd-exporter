import argparse
import cgi
import ipaddress
import socket
import urllib
import wsgiref.simple_server
import wsgiref.util

import prometheus_client

import igd
import wsgiext

def main():
    '''
    You are here.
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('--bind-address', type=ipaddress.ip_address, default='::', help='IPv6 or IPv4 address to listen on')
    parser.add_argument('--bind-port', type=int, default=9196, help='Port to listen on')
    parser.add_argument('--bind-v6only', type=int, choices=[0, 1], help='If 1, prevent IPv6 sockets from accepting IPv4 connections; if 0, allow; if unspecified, use OS default')
    parser.add_argument('--thread-count', type=int, help='Number of request-handling threads to spawn')
    args = parser.parse_args()

    server = wsgiref.simple_server.make_server(str(args.bind_address), args.bind_port, wsgi_app, wsgiext.server_class(args.bind_address, args.bind_v6only, args.thread_count))
    server.serve_forever(poll_interval=600)

def wsgi_app(environ, start_response):
    '''
    Base WSGI application that routes requests to other applications.
    '''
    name = wsgiref.util.shift_path_info(environ)
    if name == '':
        return front(environ, start_response)
    if name == 'probe':
        return probe(environ, start_response)
    elif name == 'metrics':
        return prometheus_app(environ, start_response)
    return not_found(environ, start_response)

def front(environ, start_response):
    '''
    Front page, containing links to the expoter's own metrics, as well as links
    to probe discovered devices.
    '''
    global targets

    start_response('200 OK', [('Content-Type', 'text/html')])

    if environ['REQUEST_METHOD'] == 'POST':
        form = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ, strict_parsing=1, encoding='latin1')
        if form.getfirst('search') == '1':
            targets = igd.search(5)

    return [
        b'<html>'
            b'<head><title>WSG exporter</title></head>'
            b'<body>'
                b'<h1>IGD Exporter</h1>',
                b'<form method="post"><p><input type="hidden" name="search" value="1"><button type="submit">Search</button> for devices on local network (5 second timeout)</input></form>',
                *[b'<p><a href="/probe?target=%s">Probe %s</a>' % (urllib.parse.quote_plus(target).encode('latin1'), target.encode('latin1')) for target in targets],
                b'<p><a href="/metrics">Metrics</a>'
            b'</body>'
        b'</html>'
    ]

# Discovered devices are kept in this list.
targets = []

def probe(environ, start_response):
    '''
    Performs a probe using the given root device URL.
    '''
    qs = urllib.parse.parse_qs(environ['QUERY_STRING'])
    body = igd.probe(qs['target'][0])
    start_response('200 OK', [('Content-Type', 'text/plain; charset=utf-8; version=0.0.4')])
    return body

prometheus_app = prometheus_client.make_wsgi_app()

def not_found(environ, start_response):
    '''
    How did we get here?
    '''
    start_response('404 Not Found', [('Content-Type', 'text/plain')])
    return [b'Not Found\r\n']

if __name__ == '__main__':
    main()
