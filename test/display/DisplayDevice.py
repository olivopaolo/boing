#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# test/display/DisplayDevice.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import getopt
import sys

from boing.display.DisplayDevice import DisplayDevice

try:
    opts, args = getopt.getopt(sys.argv[1:], "h", ['help'])
except getopt.GetoptError as err:
    print(str(err)) # will print something like "option -a not recognized"
    print("usage: %s [<url>]"%sys.argv[0])
    print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
    sys.exit(2)

for o, a in opts:
    if o in ("-h", "--help"):
        print("usage: %s [<url>]"%sys.argv[0])
        print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
        print("""
Open a display device and print its statistics.

Options:
 -h, --help                 display this help and exit
 
Available URLs: 
 dummy:[?ppi=96&hz=60&bx=0&by=0&bw=0&bh=0&w=0&h=0]
   Dummy device with specified resolution, bounds and size.

 any: 	
   Any of the platform-specific devices below.

 xorgdisplay:[<display name>]
   The specified X11 display of the form [hostname]:displaynumber[.screennumber].
   (LINUX ONLY)

 windisplay:
   Specific display device for MS Windows OS.
   (WINDOWS ONLY)
""")
        sys.exit(0)

url = args[0] if len(args)>0 else None
display = DisplayDevice.create(url)
display.debug()
