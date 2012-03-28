#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# test/boing.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import argparse
import itertools
import traceback
import signal
import sys

from PyQt4 import QtCore, QtGui
from boing.nodes.NodeLoader import NodeLoader

# Parse arguments
parser = argparse.ArgumentParser(
    description="Redirects many input sources to many outputs.")
parser.add_argument("-i", dest="input", nargs="+", default=[],
                    help="define the inputs")
parser.add_argument("-o", dest="output", nargs="+", default=[],
                    help="define the outputs")
parser.add_argument("-C", dest="console", nargs="?", default=False, const="std:",
                    metavar="HOST:PORT", help="Activate console")
args = parser.parse_args()

# Init application
QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("plastique"))
app = QtGui.QApplication(sys.argv)
# Reenable Ctrl-C to quit the application
timer = QtCore.QTimer(timeout=lambda: None)
timer.start(150)
signal.signal(signal.SIGINT, lambda *args: app.quit())

# Check minimal resources
if not args.input and args.console!="std:":
    default = "stdin:"
    print("Using default input:", default)    
    args.input.append(default)
if not args.output:
    default = "stdout:"
    print("Using default output:", default)
    args.output.append(default)

# Create nodes
inputs = []
for url in args.input:
    try:
        i = NodeLoader(url, "in")
    except Exception:
        traceback.print_exc()
    else:
        inputs.append(i)
outputs = []
for url in args.output:
    try:
        o = NodeLoader(url, "out")
    except Exception:
        traceback.print_exc()
    else:
        outputs.append(o)
if not inputs: print("WARNING: No input nodes.")
if not outputs: print("WARNING: No output nodes.")

# Connect inputs to outputs
for input_, output in itertools.product(inputs, outputs):
    input_.addObserver(output)

# Setup console
if args.console:
    from boing.nodes.debug import Console, dumpGraph
    if args.console=="std:":
        import boing.utils.fileutils as fileutils
        console = Console(fileutils.CommunicationDevice(sys.stdin),
                          fileutils.IODevice(sys.stdout))
        console.addCommand("dump", dumpGraph, help="Dump node graph.",
                           origins=inputs, fd=console.outputDevice())
    else:
        import boing.net.tcp as tcp
        def newConnection(): 
            socket = consoleserver.nextPendingConnection()
            console = Console(socket, socket, parent=consoleserver)
            console.addCommand("dump", dumpGraph, help="Dump node graph.",
                               origins=inputs, fd=console.outputDevice())
        host, separator, port = args.console.partition(":")
        if not port:
            raise ValueError("Invalid console URL: %s"%args.console)
        consoleserver = tcp.TcpServer(host, port, newConnection=newConnection)
        print("Boing's console listening at %s."%consoleserver.url())

# Run
rvalue = app.exec_()
print("Exiting...")
sys.exit(rvalue)
