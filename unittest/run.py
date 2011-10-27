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
 dns_sd, display, eventloop, tcp, udp
""")
        sys.exit(0)

list = []
if len(sys.argv)==1 or 'eventloop' in sys.argv:
    from eventloop import test_ReactiveObject, test_ProducerConsumer
    list += test_ReactiveObject.suite()
    list += test_ProducerConsumer.suite()
if len(sys.argv)==1 or 'display' in sys.argv:
    from display import test_DisplayDevice
    list += test_DisplayDevice.suite()
if len(sys.argv)==1 or 'dns_sd' in sys.argv:
    from dns_sd import test_dns_sd
    list += test_dns_sd.suite()
"""if len(sys.argv)==1 or 'osc' in sys.argv:
    from osc import test_osc
    list += test_osc.suite()"""
if len(sys.argv)==1 or 'tcp' in sys.argv:
    from tcp import test_TcpServer, test_TcpSocket
    list += test_TcpServer.suite()
    list += test_TcpSocket.suite()
if len(sys.argv)==1 or 'udp' in sys.argv:
    from udp import test_UdpSocket
    list += test_UdpSocket.suite()
alltests = unittest.TestSuite(list)
runner = unittest.TextTestRunner()
runner.run(alltests)
