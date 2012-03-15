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
    print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
    sys.exit(2)

for o, a in opts:
    if o in ("-h", "--help"):
        print("usage: %s [<module>...]"%sys.argv[0])
        print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
        print("""
If no module is specified, all modules are tested; otherwise only the
specified modules will be executed. 
 
Available modules: 
 dns_sd, core, json, osc, slip, tcp, udp, utils
""")
        sys.exit(0)

list = []
if len(sys.argv)==1 or 'dns_sd' in sys.argv:
    from net import test_dns_sd
    list += test_dns_sd.suite()
if len(sys.argv)==1 or 'core' in sys.argv:
    from core import test_ReactiveObject
    list += test_ReactiveObject.suite()
if len(sys.argv)==1 or 'json' in sys.argv:
    from net import test_json
    list += test_json.suite()
if len(sys.argv)==1 or 'osc' in sys.argv:
    from net import test_osc
    list += test_osc.suite()
if len(sys.argv)==1 or 'slip' in sys.argv:
    from net import test_slip
    list += test_slip.suite()
if len(sys.argv)==1 or 'tcp' in sys.argv:
    from net import test_tcp
    list += test_tcp.suite()
if len(sys.argv)==1 or 'udp' in sys.argv:
    from net import test_udp
    list += test_udp.suite()
if len(sys.argv)==1 or 'utils' in sys.argv:
    from utils import test_QPath, test_display
    list += test_QPath.suite()
    list += test_display.suite()

alltests = unittest.TestSuite(list)
runner = unittest.TextTestRunner()
runner.run(alltests)
