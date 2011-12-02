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
 -i <source>                define an input source
 -o <output>                define an output
 -h, --help                 display this help and exit

Sources: 
 TUIO socket URL            grab a TUIO stream over a socket
                            (e.g. tuio://localhost:3333?rt=false)
 TUIO log URL               play a TUIO log from a file
                            (e.g. tuio:///tmp/test.osc.bz2?speed=1&loop=false&rt=false)

Outputs: 
 dump:                      dump received events to standard output.
                            (e.g. dump:?rest=diff,.*&hz=60&src=true&dest=true)
 viz:                       display gestures 
                            (e.g. viz:?hz=60&x=320&y=240)
)
""")
        """  
 MTDEV device node URL      open device using libmtdev
                            (e.g. mtdev:///dev/input/event5)

  Sources can be setup using a configuration file, which can be defined
  specifying the parameter "conf" in the url path. 
  (e.g. tuio://ipad@localhost:3333?conf=./test/multitouch/tuiopad.conf)

  The "rt" parameter (i.e. reception time) defines how events' timetag is
  determined.  If true the timetag is determined as the moment when the
  event is received, instead of using the moment when the event was
  generated.
  """
        sys.exit(0)
    elif o=="-i": sources.append(a)
    elif o=="-o": outputs.append(a)

# Check minimal resources
if not sources:
    print("No input source.")
    sys.exit(0)
# Init outputs
if not outputs: outputs.append("dump:")
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
rvalue = app.exec_()
print("Exiting...")
# Close all
sys.exit(rvalue)