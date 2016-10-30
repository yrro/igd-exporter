import collections
import concurrent.futures
import functools
import io
import urllib

from xml.etree import ElementTree
from xml.etree.ElementTree import Element as E, SubElement as sE, ElementTree as ET, QName

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
     pass

def probe(target_url):
    device = probe_device(target_url)

    result = []
    with concurrent.futures.ThreadPoolExecutor(4) as e:
        for metric, value in e.map(lambda metric: (metric, probe_metric(device.url, metric)), ['TotalBytesReceived', 'TotalBytesSent', 'TotalPacketsReceived', 'TotalPacketsSent']):
            if value < 0:
                continue
            result.append(b'igd_WANDevice_1_WANCommonInterfaceConfig_1_%s{udn="%s"} %d\n' % (metric.encode('utf-8'), device.udn.encode('utf-8'), value))

    return result

def probe_device(target_url):
    with urllib.request.urlopen(target_url) as root:
        st = ElementTree.parse(root)

    url_base = st.findtext('d:URLBase', namespaces=ns)
    device = st.find("d:device[d:deviceType='urn:schemas-upnp-org:device:InternetGatewayDevice:1']/d:deviceList/d:device[d:deviceType='urn:schemas-upnp-org:device:WANDevice:1']", ns)
    url_path = device.findtext("d:serviceList/d:service[d:serviceType='urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1']/d:controlURL", namespaces=ns)

    return Device(device.findtext('d:UDN', namespaces=ns), urllib.parse.urljoin(url_base, url_path))

def probe_metric(service_url, metric):
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

