#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# test/osc/endpoint.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import getopt
import logging
import sys

from boing import osc
from boing.eventloop.EventLoop import EventLoop
from boing.eventloop.ProducerConsumer import Consumer
from boing.osc.OscEndpoint import OscEndpoint
from boing.url import URL

try:
    opts, args = getopt.getopt(sys.argv[1:], "l:h", ('help',))
except getopt.GetoptError as err:
    print(str(err)) # will print something like "option -a not recognized"
    print("usage: %s [-l <logging-level>] <url>"%sys.argv[0])
    print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
    sys.exit(2)
logginglevel = "WARNING"
for o, a in opts:
    if o in ("-h", "--help"):
        print("usage: %s [-l <logging-level>] <url>"%sys.argv[0])
        print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
        print("""
Dump OSC packets received at the UDP/TCP socket specified by url.

Options:
 -l <logging-level>         set logging level
 -h, --help                 display this help and exit
 """)
        sys.exit(0)
    elif o=="-l": logginglevel = a

if len(args)<1:
    print("usage: %s [-l <logging-level>] <url>"%sys.argv[0])
    print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
    sys.exit(1)

logging.basicConfig(level=logging.getLevelName(logginglevel))

class DumpConsumer(Consumer):
    def __init__(self, hz=None):
        super().__init__(hz)
    def _consume(self, products, producer):
        for p in products:
            if isinstance(p, osc.Packet):
                p.debug(sys.stdout)

url = URL(args[0])
if url.scheme.endswith("udp"):

    from boing.udp.UdpSocket import UdpListener
    endpoint = OscEndpoint(UdpListener(url))
    consumer = DumpConsumer()
    consumer.subscribeTo(endpoint)
    print("Listening on", endpoint.url())
    rvalue = EventLoop.run()
    del endpoint
    print()
    sys.exit(rvalue)
    
elif url.scheme.endswith("tcp"):

    from PyQt4 import QtCore
    from boing.tcp.TcpServer import TcpServer
    from boing.tcp.TcpSocket import TcpSocket
    def newclient():
        socket = server.nextPendingConnection()
        logger.debug("New client: %s"%str(socket.peerName()))
        socket.disconnected.connect(signalMapper.map)
        endpoint = OscEndpoint(socket)
        endpoints[socket] = endpoint
        consumer.subscribeTo(endpoint)
        signalMapper.setMapping(socket, id(socket))
    def lostclient(id_):
        socket = signalMapper.mapping(id_)
        logger.debug("Lost client: %s"%str(socket.peerName()))
        socket.close()
        del endpoints[socket]
    endpoints = {}
    consumer = DumpConsumer()
    logger = logging.getLogger("Logger")
    signalMapper = QtCore.QSignalMapper()
    signalMapper.mapped.connect(lostclient)
    server = TcpServer(url.site.host, url.site.port)
    server.newConnection.connect(newclient)
    print("Listening at", server.url())
    rvalue = EventLoop.run()
    del server, endpoints
    print()
    sys.exit(rvalue)
    
else:
    print("Unsupported url:", url)
    sys.exit(-1)
