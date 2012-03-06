#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# test/boing.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import itertools
import getopt
import signal
import sys

from PyQt4 import QtGui

from boing.url import URL
import boing.utils.NodeLoader as loader

# configuration parameters
inurl = []
outurl = []
try:
    opts, args = getopt.getopt(sys.argv[1:], "i:o:h", ['help'])
except getopt.GetoptError as err:
    print(str(err)) # will print something like "option -a not recognized"
    name = "boing"
    print("usage: %s [-i <input>]... [-o <output>]..."%name)
    print("       %s [-h, --help]"%(" "*len(name)))
    sys.exit(2)
for o, a in opts:
    if o in ("-h", "--help"):
        name = "boing"
        print("usage: %s [-i <input>]... [-o <output>]..."%name)
        print("       %s [-h, --help]"%(" "*len(name)))
        print()
        print("""Redirects many input sources to many outputs.

Options:
 -i <input>           define an input
 -o <output>          define an output
 -h, --help           display this help and exit
""")
        sys.exit(0)
    elif o=="-i": inurl.append(URL(a))
    elif o=="-o": outurl.append(URL(a))

# Init application
QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("plastique"))
app = QtGui.QApplication(sys.argv)
signal.signal(signal.SIGINT, lambda *args: app.quit())

# Check minimal resources
if not inurl: 
    default = "stdin:"
    print("Using default input:", default)    
    inurl.append(URL(default))
if not outurl:
    default = "stdout:"
    print("Using default output:", default)
    outurl.append(URL(default))

inputs = []
for url in inurl:
    url.scheme = ".".join(("in", url.scheme))
    i = loader.NodeLoader(url)
    if i is not None: inputs.append(i)
outputs = []
for url in outurl:
    url.scheme = ".".join(("out", url.scheme))
    o = loader.NodeLoader(url)
    if o is not None: outputs.append(o)

rvalue = 0
if outputs and inputs:
    # Connect inputs to outputs
    for input_, output in itertools.product(inputs, outputs):
        input_.addObserver(output)
    # Run
    rvalue = app.exec_()
print("Exiting...")
sys.exit(rvalue)




'''
Sources: 
 JSON socket URL      read JSON stream from socket
                       e.g. "json://localhost:7777"
 TUIO socket URL      read TUIO stream from socket
                       e.g. "tuio://localhost:3333?rt=False&func=None"
 TUIO log URL         play a TUIO log from file
                       e.g. "tuio:///tmp/test.osc.bz2?speed=1&loop=False&rt=False"
 MTDEV device URL     open input device using libmtdev (LINUX ONLY)
                       e.g. "mtdev:///dev/input/event5?func=None"

 If "rt" (i.e. reception time) is true, the event's timetag is the
 time when the event is received, otherwise the OSC bundle
 timestamp is considered.

 The parameter "func" can be used to add a function for calculating 
 specific gesture attributes. 
  Available functions: rel_speed

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
         
  Sources can be setup using a configuration file, which can be defined
  specifying the parameter "conf" in the url path. 
  (e.g. tuio://ipad@localhost:3333?conf=./test/multitouch/tuiopad.conf)

'''
