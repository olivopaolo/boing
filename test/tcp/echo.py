#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# test/tcp/echo.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import logging
import getopt
import sys

from boing.eventloop.EventLoop import EventLoop
from boing.tcp.EchoServer import EchoServer

try:
    opts, args = getopt.getopt(sys.argv[1:], "o:p:l:h", 
                               ('help', 'host=', 'port='))
except getopt.GetoptError as err:
    print(str(err)) # will print something like "option -a not recognized"
    print("usage: %s [options]"%sys.argv[0])
    sys.exit(2)
args = {}
logginglevel = "WARNING"
for o, a in opts:
    if o in ("-h", "--help"):
        print("usage: %s [options]"%sys.argv[0])
        print("""
Create a TCP echo server.

Options:
 -o, --host= <host>         set server host
 -p, --port= <port>         set server port
 -l <logging-level>         set logging level
 -h, --help                 display this help and exit
 """)
        sys.exit(0)
    elif o=="-l": logginglevel = a
    elif o in ("-o", "--host"): args["addr"] = a
    elif o in ("-p", "--port"): args["port"] = a

logging.basicConfig(level=logging.getLevelName(logginglevel))
server = EchoServer(**args)
print("EchoServer listening at", server.url())
rvalue = EventLoop.run()
del server
print()
sys.exit(rvalue)
