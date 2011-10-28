#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# test/utils/netcat.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import getopt
import logging
import sys

from boing.eventloop.EventLoop import EventLoop
from boing.utils.SocketEndpoint import SocketEndpoint
from boing.url import URL

try:
    opts, args = getopt.getopt(sys.argv[1:], "l:h", ('help',))
except getopt.GetoptError as err:
    print(str(err)) # will print something like "option -a not recognized"
    print("usage: %s [-l <logging-level>] <url> [<redirect-url>]"%sys.argv[0])
    print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
    sys.exit(2)
logginglevel = "WARNING"
for o, a in opts:
    if o in ("-h", "--help"):
        print("usage: %s [-l <logging-level>] <url> [<redirect-url>]"%sys.argv[0])
        print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
        print("""
Dump or redirect packets received at the UDP/TCP socket specified by url.

Options:
 -l <logging-level>         set logging level
 -h, --help                 display this help and exit
 """)
        sys.exit(0)
    elif o=="-l": logginglevel = a

if len(args)<1:
    print("usage: %s [-l <logging-level>] <url> [<redirect-url>]"%sys.argv[0])
    print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
    sys.exit(1)

logging.basicConfig(level=logging.getLevelName(logginglevel))
from boing.eventloop.ProducerConsumer import Consumer
class DumpConsumer(Consumer):
    def _consume(self, products, producer):
        for p in products:
            data = p.get("data")
            if data is not None: print(data)

url = URL(args[0])
if url.scheme.endswith("udp"):

    from boing.udp.UdpSocket import UdpListener
    source = SocketEndpoint(UdpListener(url))
    print("Listening at", source.socket().url())
    if len(args)>1:
        outputurl = URL(args[1])
        if outputurl.scheme.endswith("udp"):
            from boing.udp.UdpSocket import UdpSender
            socket = UdpSender(outputurl)
        elif outputurl.scheme.endswith("tcp"):
            from boing.tcp.TcpSocket import TcpConnection
            socket = TcpConnection(outputurl)
            socket.disconnected.connect(EventLoop.stop)
            #socket.setOption("nodelay")
        else:
            print("Unsupported outputurl:", outputurl)
            sys.exit(-1)
        output = SocketEndpoint(socket)
        output.subscribeTo(source)
        print("Redirecting to", outputurl)
    else:
        output = DumpConsumer()
        output.subscribeTo(source)
    rvalue = EventLoop.run()
    del source, output
    print()
    sys.exit(rvalue)
       
elif url.scheme.endswith("tcp"):

    from boing.tcp.TcpServer import TcpServer
    from boing.tcp.TcpSocket import TcpSocket
    def newclient():
        conn = server.nextPendingConnection()
        logger.debug("New client: %s"%str(conn.peerName()))
    class RedirectSocket(TcpSocket):
        def __init__(self, parent=None):
            TcpSocket.__init__(self, parent)
            self.endpoint = SocketEndpoint(self)
            output.subscribeTo(self.endpoint)
            self.disconnected.connect(self.__disconnected)
        def __disconnected(self):
            logger.debug("Lost client: %s"%str(self.peerName()))
    server = TcpServer(url.site.host, url.site.port, factory=RedirectSocket)
    server.newConnection.connect(newclient)
    print("Listening at", server.url())
    if len(args)>1:
        outputurl = URL(args[1]) 
        if outputurl.scheme.endswith("udp"):
            from boing.udp.UdpSocket import UdpSender
            socket = UdpSender(outputurl)
        elif outputurl.scheme.endswith("tcp"):
            from boing.tcp.TcpSocket import TcpConnection
            socket = TcpConnection(outputurl)
            socket.disconnected.connect(EventLoop.stop)
        else:                
            print("Unsupported outputurl:", outputurl)
            sys.exit(-1)
        output = SocketEndpoint(socket)
        print("Redirecting to", outputurl)
    else: 
        output = DumpConsumer()
    logger = logging.getLogger("Logger")
    rvalue = EventLoop.run()
    del server
    print()
    sys.exit(rvalue)
    
else:
    print("Unsupported url:", url)
    sys.exit(-1)
