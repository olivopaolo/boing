#!/usr/bin/env python3

# -*- coding: utf-8 -*-
#
# boing/run.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import argparse
import itertools
import logging
import traceback
import signal
import sys

from PyQt4 import QtCore, QtGui

import boing

# Parse arguments
parser = argparse.ArgumentParser(
    description="Redirects many input sources to many outputs.")
parser.add_argument("-i", dest="input", nargs="+", default=[],
                    help="define the inputs")
parser.add_argument("-o", dest="output", nargs="+", default=[],
                    help="define the outputs")
parser.add_argument("-C", dest="console", nargs="?", default=False, 
                    const="std:", metavar="HOST:PORT", 
                    help="Activate console")
parser.add_argument("-L", dest="logging_level",
                    default="INFO", metavar="LEVEL", 
                    help="Set logging level")
parser.add_argument("-T", dest="traceback", nargs="?", type=int, 
                    default=0, const=99, metavar="INTEGER", 
                    help="Set exceptions traceback depth")
args = parser.parse_args()
logging.basicConfig(level=logging.getLevelName(args.logging_level))

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
    logging.info("Using default input: %s"%default)    
    args.input.append(default)
if not args.output:
    default = "stdout:"
    logging.info("Using default output: %s"%default)
    args.output.append(default)

# Create nodes
inputs = []
for url in args.input:
    try:
        i = boing.create(url, "in")
    except Exception as exc:
        logging.error(exc)
        if args.traceback: traceback.print_exc(args.traceback)
    else:
        inputs.append(i)
outputs = []
for url in args.output:
    try:
        o = boing.create(url, "out")
    except Exception as exc:
        logging.error(exc)
        if args.traceback: traceback.print_exc(args.traceback)
    else:
        outputs.append(o)
if not inputs: logging.warning("No input nodes.")
if not outputs: logging.warning("No output nodes.")

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
        logging.info("Boing's console listening at %s."%consoleserver.url())

# Run
rvalue = app.exec_()
logging.debug("Exiting...")
sys.exit(rvalue)
