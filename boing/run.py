#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# boing/run.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

# FIXME: This file should be placed into direcotry boing/bin, but
# configure.py won't be able to consider it as a script.

import argparse
import itertools
import logging
import traceback
import signal
import sys

from PyQt4 import QtCore, QtGui

import boing
import boing.utils

# Parse arguments
parser = argparse.ArgumentParser(
    description="Redirects many input sources to many outputs.")
parser.add_argument("-i", dest="input", nargs="+", default=[],
                    help="define the inputs")
parser.add_argument("-o", dest="output", nargs="+", default=[],
                    help="define the outputs")
parser.add_argument("-C", dest="console", nargs="?", default=None, 
                    const="", metavar="HOST:PORT", 
                    help="Activate console")
parser.add_argument("-G", dest="graph", nargs="?", default=None, 
                    const="stdout:", metavar="URI", 
                    help="Activate graph view (e.g. -G stdout:)")
parser.add_argument("-L", dest="logging_level",
                    default="INFO", metavar="LEVEL", 
                    help="Set logging level")
parser.add_argument("-T", dest="traceback", nargs="?", type=int, 
                    default=0, const=99, metavar="INTEGER", 
                    help="Set exceptions traceback depth")
parser.add_argument("-f", dest="force", action='store_true',
                    help="Force execution (avoiding warnings)")
parser.add_argument("--version", action='store_true',
                    help="Output version and copyright information")
args = parser.parse_args()

if args.version: 
    print(
        """Boing (version %s)

Copyright (C) 2012 Paolo Olivo and Nicolas Roussel
This is free software; see the source for copying conditions. There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE."""%boing.VERSION)
    sys.exit(0)
logging.basicConfig(level=logging.getLevelName(args.logging_level))

# Init application
QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("plastique"))
app = QtGui.QApplication(sys.argv)
# Reenable Ctrl-C to quit the application
timer = QtCore.QTimer(timeout=lambda: None)
timer.start(150)
signal.signal(signal.SIGINT, lambda *args: app.quit())

# Check minimal resources
if not args.input and args.console!="":
    default = "stdin:"
    logging.info("Using default input: %s"%default)    
    args.input.append(default)
if not args.output:
    default = "stdout:"
    logging.info("Using default output: %s"%default)
    args.output.append(default)

# Create nodes
inputs = []
for expr in args.input:
    try:
        uris = expr.split("+")
        i = sum((boing.create(uri, "in") for uri in uris), None)
    except Exception as exc:
        logging.error(exc)
        if args.traceback: traceback.print_exc(args.traceback)
    else:
        inputs.append(i)
outputs = []
for expr in args.output:
    try:
        uris = expr.split("+")
        o = sum((boing.create(uri, "out") for uri in uris), None)
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

if args.graph:
    # Setup graph view
    node = boing.create("grapher."+args.graph)
    node.grapher.setStarters(inputs)

if args.console is not None:
    # Setup console
    local = {"__name__": "__console__", 
             "__doc__": None,
             "boing": boing,
             "inputs": inputs, "outputs": outputs,
             }
    if not args.console:
        console = boing.activateConsole(args.console, local)
    else:    
        host, separator, port = args.console.partition(":")
        if not port:
            raise ValueError("Socket port is mandatory: %s"%args.console)
        if not host: host = "127.0.0.1"
        elif host not in ("127.0.0.1", "localhost", "::1") and not args.force:
            host = "127.0.0.1"
            logging.warning(
                "It's unsafe to open interpreter on a network socket. "+
                "Using '127.0.0.1' instead (Try -f to force)")
        console = boing.activateConsole("tcp://%s:%s"%(host, port), local)
        logging.info("Boing's console listening at %s."%console.url())

# Run
rvalue = app.exec_()
logging.debug("Exiting...")
sys.exit(rvalue)
