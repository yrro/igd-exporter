import collections
import concurrent.futures
import contextlib
import io
import itertools
import socket
import traceback
import urllib.request
import urllib.parse
import wsgiref.headers

import prometheus_client

from xml.etree import ElementTree
from xml.etree.ElementTree import Element as E, SubElement as sE, ElementTree as ET, QName

metrics = {
    'TotalBytesReceived': 'Count of bytes received by all WAN{PPP/IP}Connections',
    'TotalBytesSent': 'Count of bytes transmitted by all WAN{PPP/IP}Connections',
    'TotalPacketsReceived': 'Count of packets recieved by all WAN{PPP/IP}Connections',
    'TotalPacketsSent': 'Count of packets transmitted by all WAN{PPP/IP}Connections'
}

ns = {
    'd': 'urn:schemas-upnp-org:device-1-0',
    's': 'http://schemas.xmlsoap.org/soap/envelope',
    'i': 'urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1',
}

# Any other values causes my IGD to close the connection before sending a
# response.
ElementTree.register_namespace('s', ns['s'])
ElementTree.register_namespace('u', ns['i'])

class Device(collections.namedtuple('Device', ['udn', 'url'])):
    '''
    Collects interesting attributes about a device.

    udn - Unique Device Name, should uniquely identify the WANDevice

    url - the Control URL for the WANCommonInterfaceConfig service attached to
          the WANDevice
    '''
    pass

def search(timeout):
    '''
    Search for devices implementing WANCommonInterfaceConfig on the network.

    Search ends the specified number of seconds after the last result (if any) was received.

    Returns an iterator of root device URLs.
    '''
    with contextlib.ExitStack() as stack:
        sockets = []
        sockets.append(stack.enter_context(socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)))
        sockets.append(stack.enter_context(socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)))

        for s in sockets:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if s.family == socket.AF_INET6:
                s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)

            with concurrent.futures.ThreadPoolExecutor(len(sockets)) as ex:
                return itertools.chain.from_iterable(ex.map(lambda s: search_socket(s, timeout, ns['i']), sockets))

def search_socket(sock, timeout, target='ssdp:all'):
    '''
    Transmit an SSDP search request to the local network.

    Filters results as specified by target.

    Returns a list of root device URLs.
    '''
    addr = 'ff02::c' if sock.family == socket.AF_INET6 else '239.255.255.250'

    h = wsgiref.headers.Headers([])
    h['HOST'] = '[{}]'.format(addr) if sock.family == socket.AF_INET6 else addr
    h['MAN'] = '"ssdp:discover"'
    h['MX'] = str(timeout)
    h['ST'] = target

    with io.BytesIO() as out:
        out.write(b'M-SEARCH * HTTP/1.1\r\n')
        out.write(bytes(h))
        sock.sendto(out.getvalue(), (addr, 1900))

    result = []

    for n in range(100):
        sock.settimeout(timeout)
        try:
            buf, addr = sock.recvfrom(1024)
        except socket.timeout:
            break

        try:
            result.append(search_result(buf, addr))
        except:
            traceback.print_exc()

    return result

def search_result(buf, addr):
    '''
    Retrieve root device URL from search response
    '''
    try:
        headers, buf = search_parse(buf)
        return headers['Location']
    except:
        raise Exception('Malformed search result from {}'.format(addr))

def search_parse(buf):
    '''
    Parse a search response, returning a mapping of headers and the body.
    '''
    status, sep, buf = buf.partition(b'\r\n')
    version, status, reason = status.split()
    if status != b'200':
        raise Exception('Unknown status {}'.format(status))
    headers = wsgiref.headers.Headers([])
    while True:
        header, sep, buf = buf.partition(b'\r\n')
        if header == b'':
            break
        else:
            name, sep, value = header.partition(b':')
            headers.add_header(name.decode('latin1').strip(), value.decode('latin1').strip())

    return headers, buf

def probe(target_url):
    '''
    Returns a collector populated with metrics from the services found at the
    given root device URL.

    Metrics are labelled with the service's UDN.
    '''
    device = probe_device(target_url)
    return Collector(device)

class Collector:
    def __init__(self, device):
        self.__device = device

    def collect(self):
        with concurrent.futures.ThreadPoolExecutor(4) as ex:
            for metric, value in ex.map(lambda metric: (metric, probe_metric(self.__device.url, metric)), metrics.keys()):
                g = prometheus_client.core.GaugeMetricFamily(
                    'igd_WANDevice_1_WANCommonInterfaceConfig_1_{}'.format(metric),
                    metrics[metric],
                    labels=['udn'],
                )
                if value < 0:
                    # WANCommonInterfaceConfig:1 specifies these values with the
                    # 'ui4' data type. Assume any negative values are caused by the
                    # IGD formatting the value as a signed 32-bit integer.
                    value += 2 ** 32
                g.add_metric([self.__device.udn], value)
                yield g

def probe_device(target_url):
    '''
    Determine UDN and service control URL for the WanCommonInterfaceConfig
    service described by SCPD XML found at the given root device URL.
    '''
    with urllib.request.urlopen(target_url) as scpd:
        st = ElementTree.parse(scpd)

    url_base = st.findtext('d:URLBase', namespaces=ns)
    device = st.find("d:device[d:deviceType='urn:schemas-upnp-org:device:InternetGatewayDevice:1']/d:deviceList/d:device[d:deviceType='urn:schemas-upnp-org:device:WANDevice:1']", ns)
    url_path = device.findtext("d:serviceList/d:service[d:serviceType='urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1']/d:controlURL", namespaces=ns)

    return Device(device.findtext('d:UDN', namespaces=ns), urllib.parse.urljoin(url_base, url_path))

def probe_metric(service_url, metric):
    '''
    Query the service at the given URL for the given metric value.

    Assumptions are made about the name of the method and output parameters
    which are only valid for the WanCommonInterfaceConfig service.
    '''
    envelope = E(QName(ns['s'], 'Envelope'), {QName(ns['s'], 'encodingStyle'): 'http://schemas.xmlsoap.org/soap/encoding/'})
    body = sE(envelope, QName(ns['s'], 'Body'))
    method = sE(body, QName(ns['i'], 'Get{}'.format(metric)))
    request_tree = ET(envelope)
    with io.BytesIO() as out:
        request_tree.write(out, xml_declaration=True)
        req = urllib.request.Request(service_url, out.getvalue())

    req.add_header('Content-Type', 'text/xml')
    req.add_header('SOAPAction', '"{}#{}"'.format(ns['i'], 'Get{}'.format(metric)))

    with urllib.request.urlopen(req) as result:
        result_tree = ElementTree.parse(result)
        return int(result_tree.findtext('.//New{}'.format(metric), namespaces=ns))

if __name__ == '__main__':
    for url in search(5):
        print(url)
