#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# test/boing.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import getopt
import signal
import sys

from PyQt4.QtGui import QApplication, QStyleFactory

# Init application
QApplication.setStyle(QStyleFactory.create("plastique"))
app = QApplication(sys.argv)

from boing.eventloop.OnDemandProduction import DumpConsumer
from boing.utils.Source import Source
from boing.utils.Output import Output
from boing.tuio.TuioToState import TuioToState

# configuration parameters
sources = []
outputs = []
try:
    opts, args = getopt.getopt(sys.argv[1:], "i:o:h", ['help'])
except getopt.GetoptError as err:
    print(str(err)) # will print something like "option -a not recognized"
    print("usage: %s [-i <source>]... [-o <output>]..."%sys.argv[0])
    print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
    sys.exit(2)
for o, a in opts:
    if o in ("-h", "--help"):
        print("usage: %s [-i <source>]... [-o <output>]..."%sys.argv[0])
        print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
        print("""Redirect input streams to different outputs.

Options:
 -i <source>          define an input source
 -o <output>          define an output
 -h, --help           display this help and exit

Sources: 
 JSON socket URL      read JSON stream from socket
                       e.g. "json://localhost:7777"
 TUIO socket URL      read TUIO stream from socket
                       e.g. "tuio://localhost:3333?rt=False"
 TUIO log URL         play a TUIO log from file
                       e.g. "tuio:///tmp/test.osc.bz2?speed=1&loop=False&rt=False"

 If "rt" (i.e. reception time) is true, the event's timetag is the
 time when the event is received, otherwise the OSC bundle timestamp
 is considered.

 MTDEV device URL     open input device using libmtdev (LINUX ONLY)
                       e.g. "mtdev:///dev/input/event5"

Outputs: 
 dump:                dump received events to standard output.
                       e.g. "dump:?req=.*&hz=none&src=False&dest=False&count=False"
 stat:                print data production statistics.
                       e.g. "stat:?req=.*&clear=False&hz=1"
 viz:                 display gestures (DEFAULT)
                       e.g. "viz:?req=(diff,.*,gestures),timetag&hz=60&x=320&y=240"
 JSON socket URL      encode events and send JSON stream to socket
                       e.g. "json://[::1]:7777?req=diff,timetag"
 TUIO socket URL      redirect gesture events as a TUIO stream to a socket
                       e.g. "tuio://[::1]:3333?req=(diff,.*,gestures),timetag"
 TUIO log URL         log gesture events as a TUIO log file
                       e.g. "tuio:///tmp/test.osc.bz2?req=(diff,.*,gestures),timetag"
""")
        """  
  Sources can be setup using a configuration file, which can be defined
  specifying the parameter "conf" in the url path. 
  (e.g. tuio://ipad@localhost:3333?conf=./test/multitouch/tuiopad.conf)

"""
        sys.exit(0)
    elif o=="-i": sources.append(a)
    elif o=="-o": outputs.append(a)

# Check minimal resources
if not sources:
    print("No input source.")
    sys.exit(0)
# Init outputs
if not outputs: outputs.append("viz:")
outs = []
for url in outputs:
    o = Output(url)
    if o is not None: outs.append(o)
# Init sources
srcs = []
for url in sources:
    s = Source(url)
    if s is not None: srcs.append(s)
# Connect sources to outputs
for s in srcs:
    for o in outs:
        o.subscribeTo(s)
# Run
signal.signal(signal.SIGINT, lambda *args: app.quit())
rvalue = app.exec_()
print("Exiting...")
# Close all
sys.exit(rvalue)
