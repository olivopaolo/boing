#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# unittest/run.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import getopt
import sys
import unittest

try:
    opts, args = getopt.getopt(sys.argv[1:], "h", ('help', ))
except getopt.GetoptError as err:
    print(str(err))
    print("usage: %s [<module>...]"%sys.argv[0])
    print("       %s [--help]"%(" "*len(sys.argv[0])))
    sys.exit(2)

for o, a in opts:
    if o in ("-h", "--help"):
        print("usage: %s [<module>...]"%sys.argv[0])
        print("       %s [--help]"%(" "*len(sys.argv[0])))
        print("""
 If no module is specified, all modules are tested; otherwise only the
 specified modules will be executed. 
 
 Available modules: 
   eventloop
""")
        sys.exit(0)

list = []
if len(sys.argv)==1 or 'eventloop' in sys.argv:
    from eventloop import test_ReactiveObject
    list += test_ReactiveObject.suite()

alltests = unittest.TestSuite(list)
runner = unittest.TextTestRunner()
runner.run(alltests)
