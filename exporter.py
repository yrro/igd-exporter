import wsgiref
import urllib

import prometheus_client

import igd

def wsgi_app(environ, start_response):
    name = wsgiref.util.shift_path_info(environ)
    if name == '':
        return front(environ, start_response)
    if name == 'probe':
        return probe(environ, start_response)
    elif name == 'metrics':
        return prometheus_app(environ, start_response)
    return not_found(environ, start_response)

def front(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [
        b'<html>'
            b'<head><title>WSG exporter</title></head>'
            b'<body>'
                b'<h1>WSG Exporter</h1>'
                b'<p><a href="/probe?target=http%3A//192.0.2.1/RootDevice.xml">Probe http://192.0.2.1/RootDevice.xml</a>'
                b'<p><a href="/metrics">Metrics</a>'
            b'</body>'
        b'</html>'
    ]

def probe(environ, start_response):
    qs = urllib.parse.parse_qs(environ['QUERY_STRING'])
    body = igd.probe(qs['target'][0])
    start_response('200 OK', [('Content-Type', 'text/plain; charset=utf-8; version=0.0.4')])
    return body

prometheus_app = prometheus_client.make_wsgi_app()

def not_found(environ, start_response):
    start_response('404 Not Found', [('Content-Type', 'text/plain')])
    return [b'Not Found\r\n']

if __name__ == '__main__':
    s = wsgiref.simple_server.make_server('', 9090, wsgi_app)
    s.serve_forever()
