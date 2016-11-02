igd-exporter
============

Allows probing of UPnP Internet Gateway Devices (i.e., consumer Internet
routers) by [Prometheus](https://prometheus.io/). Modelled after the
[Blackbox exporter](https://github.com/prometheus/blackbox_exporter).

[![Build Status](https://travis-ci.org/yrro/igd-exporter.svg?branch=master)](https://travis-ci.org/yrro/igd-exporter)

Running
-------

```
$ python3 -m pip install git+https://github.com/yrro/igd-exporter.git
$ igd-exporter
```

You can then visit <http://localhost:9196/> to search for devices on your
network, and probe each discovered device to see its available metrics; for
instance:

```
igd_WANDevice_1_WANCommonInterfaceConfig_1_TotalBytesReceived{udn="uuid:upnp-WANDevice-1_0-e0f478651f51"}    340579275
igd_WANDevice_1_WANCommonInterfaceConfig_1_TotalBytesSent{udn="uuid:upnp-WANDevice-1_0-e0f478651f51"}        2098807488
igd_WANDevice_1_WANCommonInterfaceConfig_1_TotalPacketsReceived{udn="uuid:upnp-WANDevice-1_0-e0f478651f51"}  27506947
igd_WANDevice_1_WANCommonInterfaceConfig_1_TotalPacketsSent{udn="uuid:upnp-WANDevice-1_0-e0f478651f51"}      10983346
```

The ugly metric names are subject to chance as I add more of them. According to
the UPnP specification, the `udn` label *should* be unique to a given device.

Packaging
---------

To produce a Debian package:

```
$ debian/rules clean
$ dpkg-buildpackage -b
```

The `prometheus-igd-exporter` package will be created in the parent directory.

Prometheus configuration
------------------------

Each device is identified by a "root device URL", for example
`http://192.0.2.1:80/scpd.xml`. You can use relabelling to pass this URL to the
exporter as follows:

```yaml
scrape_configs:
 - job_name: igd
   metrics_path: /probe
   static_configs:
    - targets: ['http://192.0.2.1:80/scpd.xml']
   relabel_configs:
    - source_labels: [__address__]
      target_label: __param_target
    - source_labels: [__param_target]
      target_label: instance
    - target_label: __address__
      replacement: exporter-host:9196
```

Exporter Configuration
----------------------

Some useful options can be given to `exporter.py` on the command line.

```
$ igd-exporter
usage: igd-exporter [-h] [--bind-address BIND_ADDRESS] [--bind-port BIND_PORT]
                    [--bind-v6only {0,1}] [--thread-count THREAD_COUNT]

optional arguments:
  -h, --help            show this help message and exit
  --bind-address BIND_ADDRESS
                        IPv6 or IPv4 address to listen on
  --bind-port BIND_PORT
                        Port to listen on
  --bind-v6only {0,1}   If 1, prevent IPv6 sockets from accepting IPv4
                        connections; if 0, allow; if unspecified, use OS
                        default
  --thread-count THREAD_COUNT
                        Number of request-handling threads to spawn
```

Development
-----------

I'm trying to keep things simple and rely only on the Python standard library
and the [prometheus_client](https://github.com/prometheus/client_python)
module.

To run `exporter` from source:

```
$ python3 -m pip install -e .
$ igd-exporter
```

or, without installing:


```
$ python3 -m igd_exporter
```
