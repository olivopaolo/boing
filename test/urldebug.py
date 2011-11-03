#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# test/urldebug.py -
#
# Authors: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import getopt
import sys

from boing.url import URL

try:
    opts, args = getopt.getopt(sys.argv[1:], "h", ('help',))
except getopt.GetoptError as err:
    print(err)
    print("usage: %s <urls>"%sys.argv[0])
    print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
    sys.exit(2)
    
for o, a in opts:
    if o in ("-h", "--help"):
        print("usage: %s <urls>"%sys.argv[0])
        print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
        print("""
Print urls' debug details.

Options:
 -h, --help                  display this help and exit
  """)
        sys.exit(0)

if not len(args):
    print("usage: %s <urls>"%sys.argv[0])
    print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
    sys.exit(2)
for u in args:
        print('-'*40)
        print(u)
        url = URL(u)
        print(url)
        print()
        url.debug()
        print()
