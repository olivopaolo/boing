#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# test/osc/recplay.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import getopt
import sys

from PyQt4 import QtCore

from boing.eventloop.EventLoop import EventLoop
from boing.utils.File import File
from boing.url import URL

try:
    opts, args = getopt.getopt(sys.argv[1:], "h", ('help',))
except getopt.GetoptError as err:
    print(str(err)) # will print something like "option -a not recognized"
    print("usage: %s record <host> <file>"%sys.argv[0])
    print("       %s play|loop <file> <host>"%(" "*len(sys.argv[0])))
    print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
    sys.exit(2)
for o, a in opts:
    if o in ("-h", "--help"):
        print("usage: %s record <host> <file>"%sys.argv[0])
        print("       %s play|loop <file> <host>"%(" "*len(sys.argv[0])))
        print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
        print("""
Record an OSC stream received at an UDP/TCP socket or send a recorded
stream to a target UDP/TCP socket.

Options:
 -h, --help                 display this help and exit
 """)
        sys.exit(0)

try:
    action = args[0].lower()
    if action not in ("record", "play", "loop"): raise ValueError()
    if action in ("play", "loop"):
        fileurl = URL(args[1])
        hosturl = URL(args[2])
    else: 
        fileurl = URL(args[2])
        hosturl = URL(args[1])
except IndexError or  ValueError:
    print("usage: %s record <host> <file>"%sys.argv[0])
    print("       %s play|loop <file> <host>"%(" "*len(sys.argv[0])))
    print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
    sys.exit(1)

if action=="record":

    import datetime
    from boing.osc.LogFile import LogFile
    # Init output file
    if fileurl.kind in (URL.ABSPATH, URL.RELPATH) or fileurl.scheme=="file":
        file_ = File(fileurl, File.WriteOnly)
    else:
        print("Unsupported url:", fileurl)
        sys.exit(-1)
    output = LogFile(file_)
    # Init source 
    if hosturl.scheme=="osc":
        print("warning: no transport protocol specified in URL, assuming UDP.")
        hosturl.scheme="osc.udp"
    if hosturl.scheme.endswith("udp"):
        from boing.udp.UdpSocket import UdpListener
        from boing.utils.DataIO import DataReader
        source = DataReader(UdpListener(hosturl))
        output.subscribeTo(source)
    elif hosturl.scheme.endswith("tcp"):
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
        server = TcpServer(hosturl.site.host, hosturl.site.port)
        server.newConnection.connect(newclient)
        source = None
        print("Listening at", server.url())
    else:
        print("Unsupported host url:", hosturl)
        sys.exit(-1)
    print("Logging to %s (quit the application to stop)"%(
            output.file().fileName()))
    rvalue = EventLoop.run()
    now = datetime.datetime.now()
    print("Logged %d packets in %s"%(output.cnt, now-output.t0))
    if "server" in globals(): del server
    if source: del source
    del output
    print()
    sys.exit(rvalue)

else:

    from boing.osc.LogPlayer import LogPlayer
    # Init source file
    def startPlayer():
        source.start(looping=(action=="loop"))
    def closer():        
        if not output.outputDevice().bytesToWrite(): EventLoop.stop()
    if fileurl.kind in (URL.ABSPATH, URL.RELPATH) or fileurl.scheme=="file":
        file_ = File(fileurl, File.ReadOnly, uncompress=True)
    else:
        print("Unsupported url:", fileurl)
        sys.exit(-1)
    source = LogPlayer(file_)
    if action=="play": source.stopped.connect(closer, QtCore.Qt.QueuedConnection)
    # Init output
    def bytesWritten(nbytes):
        if not source.isPlaying() and not output.outputDevice().bytesToWrite():
            EventLoop.stop()
    if hosturl.scheme=="osc":
        print("warning: no transport protocol specified in URL, assuming UDP.")
        hosturl.scheme="osc.udp"
    if hosturl.scheme.endswith("udp"):
        from boing.udp.UdpSocket import UdpSender
        from boing.utils.DataIO import DataWriter
        output = DataWriter(UdpSender(hosturl))
        startPlayer()
    elif hosturl.scheme.endswith("tcp"):
        from boing.tcp.TcpSocket import TcpConnection
        from boing.slip.SlipDataIO import SlipDataWriter
        socket = TcpConnection(hosturl)
        socket.connected.connect(startPlayer)
        socket.disconnected.connect(EventLoop.stop)
        output = SlipDataWriter(socket)
    else:
        print("Unsupported host url:", hosturl)
        sys.exit(-1)
    output.outputDevice().bytesWritten.connect(bytesWritten)
    output.subscribeTo(source)
    rvalue = EventLoop.run()
    del source, output
    print()
    sys.exit(rvalue)



