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

prog="boing"
# usage = """%s [--help] [--version]
#         %s<command> ..."""%(prog, " "*len(prog))
version = """Boing (version %s)

Copyright 2012, INRIA

Authors: Paolo Olivo & Nicolas Roussel

This is free software; see the source for copying conditions. There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
"""%boing.VERSION
commonargs = (
    (("-G", ), dict(dest="graph", nargs="?", default=None,
                    const="stdout:", metavar="URI",
                    help="activate pipeline plot (e.g. -G out.stdout:)")),
    (("-C", ), dict(dest="console", nargs="?", default=None,
                   const="", metavar="HOST:PORT",
                   help="activate python console")),
    (("-L", ), dict(dest="logging_level", default="INFO", metavar="LEVEL",
                   help="set logging level")),
    (("-T", ), dict(dest="traceback", nargs="?", type=int,
                   default=0, const=99, metavar="INTEGER",
                   help="set exceptions traceback depth")),
    (("-f", ), dict(dest="force", action='store_true',
                   help="force execution (avoiding warnings)")),
    )

# Init arguments parser
parser = argparse.ArgumentParser(
    prog=prog, #usage=usage,
    formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('--version', action='version', version=version)

subparsers = parser.add_subparsers(title="basic commands")
cfgparser = subparsers.add_parser(
    "cfg", help="create a pipeline from a single URI expression")
cfgparser.add_argument("config", metavar="<expr>",
                       help="define the pipeline configuration")
for argv, kwargs in commonargs:
    cfgparser.add_argument(*argv, **kwargs)
ioparser = subparsers.add_parser(
    "io", help="create a pipeline defining the inputs and the outputs")
ioparser.add_argument("-i", dest="input", nargs="+", default=[],
                      help="define the inputs")
ioparser.add_argument("-o", dest="output", nargs="+", default=[],
                      help="define the outputs")
for argv, kwargs in commonargs:
    ioparser.add_argument(*argv, **kwargs)

# Parse sys.argv
if len(sys.argv)==1: sys.argv.append("-h")
args = parser.parse_args()
logging.basicConfig(level=logging.getLevelName(args.logging_level))

# Init application
QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("plastique"))
app = QtGui.QApplication(sys.argv)
# (Reenable Ctrl-C to quit the application)
timer = QtCore.QTimer(timeout=lambda: None)
timer.start(150)
signal.signal(signal.SIGINT, lambda *args: app.quit())

# Create the pipeline depending on the requested command
if "config" in args :
    try:
        pipeline = boing.create(args.config)
    except Exception as exc:
        logging.error(exc)
        if args.traceback: traceback.print_exc(args.traceback)
else:
    # Check minimal resources
    if not args.input and args.console!="":
        default = "in.stdin:"
        logging.info("Using default input: %s"%default)
        args.input.append(default)
    if not args.output:
        default = "out.stdout:"
        logging.info("Using default output: %s"%default)
        args.output.append(default)
    # Create nodes
    inputs = None
    for expr in args.input:
        try:
            inputs |= boing.create(expr)
        except Exception as exc:
            logging.error(exc)
            if args.traceback: traceback.print_exc(args.traceback)
    outputs = None
    for expr in args.output:
        try:
            outputs |= boing.create(expr)
        except Exception as exc:
            logging.error(exc)
            if args.traceback: traceback.print_exc(args.traceback)
    if inputs is None: logging.warning("No input nodes.")
    if outputs is None: logging.warning("No output nodes.")
    # Connect inputs to outputs
    pipeline = inputs + outputs

# Handle common options
if args.graph:
    # Setup graph view
    node = boing.create("grapher."+args.graph)
    node.grapher.setStarters(inputs)

if args.console is not None:
    # Setup console
    local = {"__name__": "__console__",
             "__doc__": None,
             "boing": boing,
             "pipeline": pipeline,
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

# Run the application
rvalue = app.exec_()
logging.debug("Exiting...")
sys.exit(rvalue)
