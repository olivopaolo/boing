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
import logging
import signal
import sys

from PyQt4 import QtCore

import boing

prog="boing"

version = """Boing (version %s)

Copyright 2012, INRIA

Authors: Paolo Olivo & Nicolas Roussel

This is free software; see the source for copying conditions. There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
"""%boing.__version__

# Init arguments parser
parser = argparse.ArgumentParser(
    prog=prog, #usage=usage,
    formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("-G", dest="graph", nargs="?", default=None,
                    const="grapher:stdout?hz=1&request=*&maxdepth=none", metavar="URI",
                    help="activate pipeline plot. Default URI: grapher:stdout?hz=1&request=*&maxdepth=none")
parser.add_argument("-C", dest="console", nargs="?", default=None,
                    const="", metavar="HOST:PORT",
                    help="activate python console")
parser.add_argument("-L", dest="logging_level", default="INFO", metavar="LEVEL",
                    help="set logging level")
parser.add_argument("-T", dest="traceback", nargs="?", type=int,
                    default=0, const=99, metavar="INTEGER",
                    help="set exceptions traceback depth")
parser.add_argument("-f", dest="force", action='store_true',
                    help="force execution (avoiding warnings)")
parser.add_argument("--no-gui", dest="nogui", action='store_true',
                    help="disable GUI (for running without a display server)")
parser.add_argument('--version', action='version', version=version)
parser.add_argument("config", metavar="<expr>",
                    help="define the pipeline configuration")

# Parse sys.argv
if len(sys.argv)==1: sys.argv.append("-h")
args = parser.parse_args()
logging.basicConfig(level=logging.getLevelName(args.logging_level))

# Init application
if not args.nogui:
    from PyQt4 import QtGui
    QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("plastique"))
    app = QtGui.QApplication(sys.argv)
else:
    boing.config["--no-gui"] = True
    app = QtCore.QCoreApplication(sys.argv)
# (Reenable Ctrl-C to quit the application)
timer = QtCore.QTimer(timeout=lambda: None)
timer.start(150)
signal.signal(signal.SIGINT, lambda *args: app.quit())

# Init the pipeline
try:
    pipeline = boing.create(args.config)
except Exception as exc:
    import traceback
    logging.error(exc)
    if args.traceback: traceback.print_exc(args.traceback)

# Handle common options
if args.graph:
    # Setup graph view
    node = boing.create(args.graph)
    node.grapher.setStarters((pipeline, ))

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
