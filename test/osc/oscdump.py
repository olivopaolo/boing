#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# test/osc/oscdump.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import getopt
import sys

from PyQt4 import QtCore

from boing import osc
from boing.eventloop.EventLoop import EventLoop
from boing.eventloop.ProducerConsumer import Consumer
from boing.utils.DataIO import DataReader
from boing.url import URL

try:
    opts, args = getopt.getopt(sys.argv[1:], "h", ('help',))
except getopt.GetoptError as err:
    print(str(err)) # will print something like "option -a not recognized"
    print("usage: %s <url>"%sys.argv[0])
    print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
    sys.exit(2)
for o, a in opts:
    if o in ("-h", "--help"):
        print("usage: %s <url>"%sys.argv[0])
        print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
        print("""
Dump to stdout any OSC packet received from an UDP/TCP socket or read
from an OSC log file.

Options:
 -h, --help                 display this help and exit
 """)
        sys.exit(0)

if len(args)<1:
    print("usage: %s <url>"%sys.argv[0])
    print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
    sys.exit(1)

class DumpConsumer(Consumer):
    def _consume(self, products, producer):
        for p in products:
            data = p.get("data")
            if data: 
                packet = osc.decode(data)
                packet.debug(sys.stdout)
output = DumpConsumer()
url = URL(args[0])
# Init output
if url.scheme=="osc":
    print("warning: no transport protocol specified in URL, assuming UDP.")
    url.scheme="osc.udp"
if url.kind in (URL.ABSPATH, URL.RELPATH) or url.scheme=="file":
    from boing.slip.SlipDataIO import SlipDataReader
    from boing.utils.File import FileReader
    def closer():
        EventLoop.stop()
    source = SlipDataReader(FileReader(url, uncompress=True))
    source.inputDevice().completed.connect(closer, QtCore.Qt.QueuedConnection)
    output.subscribeTo(source)
elif url.scheme.endswith("udp"):
    from boing.udp.UdpSocket import UdpListener
    source = DataReader(UdpListener(url))
    output.subscribeTo(source)
    print("Listening at", source.inputDevice().url())
elif url.scheme.endswith("tcp"):
    from boing.tcp.TcpServer import TcpServer
    from boing.slip.SlipDataIO import SlipDataReader
    def newclient():
        conn = server.nextPendingConnection()
        global source
        if source is None:
            source = SlipDataReader(conn)
            output.subscribeTo(source)
            conn.disconnected.connect(disconnected, QtCore.Qt.QueuedConnection)
        else: conn.close()
    def disconnected():
        EventLoop.stop()
    server = TcpServer(url.site.host, url.site.port)
    server.newConnection.connect(newclient)
    source = None
    print("Listening at", server.url())
else:
    print("Unsupported url:", url)
    sys.exit(-1)
rvalue = EventLoop.run()
if "server" in globals(): del server
if source: del source
del output
print()
sys.exit(rvalue)
