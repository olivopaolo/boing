#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# test/dns_sd/browse_and_resolve.py -
#
# Authors: 
#   Nicolas Roussel (nicolas.roussel@inria.fr)
#   Paolo Olivo     (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import getopt
import logging ; logging.basicConfig(level=logging.DEBUG)
import sys

from PyQt4 import QtCore

from boing.dns_sd.DNSServiceBrowser import DNSServiceBrowser

try:
    opts, args = getopt.getopt(sys.argv[1:], "hd:", ['help', 'domain='])
except getopt.GetoptError as err:
    print(str(err))
    print("usage: %s [options] <type>"%sys.argv[0])
    sys.exit(2)
    
domain = None
for o, a in opts:
    if o in ("-h", "--help"):
        print("usage: %s [options] <type>"%sys.argv[0])
        print("""
Browse available DNS-SD services.

Options:
  -d, --domain= <domain>         set service domain name
  -h, --help                     display this help and exit
  """)
        sys.exit(0)
    elif o in ("-d", "--domain"): domain = a

if len(args) < 1:
    print("usage: %s [options] <type>"%sys.argv[0])
    sys.exit(1)
    
app = QtCore.QCoreApplication(sys.argv)

def browserEvent(event, service):
    if event=="found":
        print('Service found:')
        print("  " + service.key())
        # Add the same handler also to the service in order to get
        # 'txtupdate' and 'resolved' events
        service.addListener(browserEvent)
        service.queryTXTrecord()
        service.resolve()
    elif event=="lost":
        print('Service lost:')
        print("  " + service.key())
    elif event=="txtupdate":
        print('Event txtupdate:')
        print("  " + service.key())
        print(service.info.get(service.interface, {}).get('txt', {}))
    elif event=="resolved":
        print('Service resolved:')
        print("  " + service.key())
        print(service.info.get(service.interface, {}).get('srv', {}))
                               
regtype = args[0]
browser = DNSServiceBrowser(regtype, domain)
browser.addListener(browserEvent)
sys.exit(app.exec_())
