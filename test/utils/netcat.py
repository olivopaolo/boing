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
import os.path
import sys

from PyQt4 import QtCore

from boing.eventloop.EventLoop import EventLoop
from boing.slip.SlipDataIO import SlipDataReader, SlipDataWriter
from boing.utils.DataIO import DataWriter, DataReader
from boing.utils.IODevice import IODevice
from boing.utils.File import File
from boing.url import URL

try:
    opts, args = getopt.getopt(sys.argv[1:], "l:h", ('help',))
except getopt.GetoptError as err:
    print(str(err)) # will print something like "option -a not recognized"
    print("usage: %s [-l <source>] [<output>]"%sys.argv[0])
    print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
    sys.exit(2)
inurl = None
for o, a in opts:
    if o in ("-h", "--help"):
        print("usage: %s [-l <source>] [<output>]"%sys.argv[0])
        print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
        print("""
Redirect data from a source to an output.

Source and output can be even a TCP/UDP socket, a file or respectively
the stdin or the stdout. SLIP encode/decode is available for TCP
sockets and files.

Options:
 -l <source>                listen from the specified source
 -h, --help                 display this help and exit
 """)
        sys.exit(0)
    elif o=="-l" and inurl is None: inurl = URL(a)

#Init output
output = None
if len(args):
    def bytesWritten(nbytes):
        if source is not None \
                and not source.inputDevice().isOpen() \
                and not output.outputDevice().bytesToWrite():
            EventLoop.stop()
    outurl = URL(args[0])
    if outurl.kind in (URL.ABSPATH, URL.RELPATH) or outurl.scheme=="file":
        output = DataWriter(File(outurl, File.WriteOnly))
    if outurl.scheme=="slip.file":
        output = SlipDataWriter(File(outurl, File.WriteOnly))
    elif outurl.scheme.endswith("udp"):
        from boing.udp.UdpSocket import UdpSender
        output = DataWriter(UdpSender(outurl))
    elif outurl.scheme.endswith("tcp"):
        from boing.tcp.TcpSocket import TcpConnection
        socket = TcpConnection(outurl)
        socket.disconnected.connect(EventLoop.stop, QtCore.Qt.QueuedConnection)
        if outurl.scheme.endswith("slip.tcp"):
            output = SlipDataWriter(socket)
        else:
            output = DataWriter(socket)
    else:
        print("Unsupported output:", outurl)
        sys.exit(-1)        
    output.outputDevice().bytesWritten.connect(bytesWritten)
else:
    outurl = None
    from boing.utils.TextIO import TextWriter
    output = TextWriter(IODevice(sys.stdout))
# Init source
if inurl is None:
    from boing.utils.TextIO import TextReader
    from boing.utils.IODevice import CommunicationDevice
    source = TextReader(CommunicationDevice(sys.stdin))
    output.subscribeTo(source)
    print("Reading from sys.stdin")
else:
    if inurl.kind in (URL.ABSPATH, URL.RELPATH) \
            or inurl.scheme in ("file", "slip.file"):
        filepath = str(inurl.path)
        if os.path.isfile(filepath):
            # Regular file
            from boing.utils.File import FileReader
            def closer():
                if not output.outputDevice().bytesToWrite(): EventLoop.stop()
                source.inputDevice().close()
            if inurl.scheme=="slip.file":
                source = SlipDataReader(FileReader(inurl))
            else:
                source = DataReader(FileReader(inurl))
            source.inputDevice().completed.connect(closer, 
                                                   QtCore.Qt.QueuedConnection)
            if outurl and outurl.scheme.endswith("tcp"): 
                output.outputDevice().connected.connect(source.inputDevice().start)
            else:
                source.inputDevice().start()
            if outurl: print("Reading from", source.inputDevice().fileName())
        elif os.path.exists(filepath):            
            from boing.utils.File import CommunicationFile
            source = DataReader(CommunicationFile(inurl))
            if outurl: print("Reading from", inurl)
        output.subscribeTo(source)
    elif inurl.scheme.endswith("udp"):
        from boing.udp.UdpSocket import UdpListener
        source = DataReader(UdpListener(inurl))
        output.subscribeTo(source)
        print("Listening at", source.inputDevice().url())
    elif inurl.scheme.endswith("tcp"):
        from boing.tcp.TcpServer import TcpServer
        def newclient():
            conn = server.nextPendingConnection()
            global source
            if source is None:
                global inurl
                if inurl.scheme.endswith("slip.tcp"):
                    source = SlipDataReader(conn)
                else:
                    source = DataReader(conn)
                output.subscribeTo(source)
                conn.disconnected.connect(disconnected, 
                                          QtCore.Qt.QueuedConnection)
            else: conn.close()
        def disconnected():
            if not output.outputDevice().bytesToWrite(): 
                EventLoop.stop()
            else: source.inputDevice().close()
        server = TcpServer(inurl.site.host, inurl.site.port)
        server.newConnection.connect(newclient)
        source = None
        serverurl = server.url()
        if serverurl.scheme=="tcp" and inurl.scheme.endswith("slip.tcp"):
            serverurl.scheme="slip.tcp"
        print("Listening at", serverurl)
    else:
        print("Unsupported url:", inurl)
        sys.exit(-1)
if outurl: print("Redirecting to", outurl)
rvalue = EventLoop.run()
if "server" in globals(): del server
if source: del source
del output
print()
sys.exit(rvalue)
