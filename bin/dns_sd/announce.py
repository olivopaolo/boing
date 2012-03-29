#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# test/dns_sd/announce.py -
#
# Authors: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import getopt
import logging ; logging.basicConfig(level=logging.DEBUG)
import sys

from PyQt4 import QtCore

from boing.net.dns_sd.DNSServiceAnnouncer import DNSServiceAnnouncer

try:
    opts, args = getopt.getopt(sys.argv[1:], 
                               "ho:d:t:", 
                               ['help', 'host=', 'domain=', 'txtrec='])
except getopt.GetoptError as err:
    print(err)
    print("usage: %s [options] <name> <type> <port>"%sys.argv[0])
    sys.exit(2)
    
host = domain = None
txtrec = {}
for o, a in opts:
    if o in ("-h", "--help"):
        print("usage: %s [options] <name> <type> <port>"%sys.argv[0])
        print("""
Announce a service using DNS-SD.

Options:
 -o, --host= <host>          set service host name
 -d, --domain= <domain>      set service domain name
 -t, --txtrec= <record>      set txt record value (e.g. "{'name':'example'}")
 -h, --help                  display this help and exit
  """)
        sys.exit(0)
    elif o in ("-o", "--host"): host = a
    elif o in ("-d", "--domain"): domain = a
    elif o in ("-t", "--txtrec"): 
        try:
            import ast
            txtrec = ast.literal_eval(a)
        except Exception:
            logging.warning("txtrec value unreadable format: %s"%a)
            txtrec = {}

if len(args) < 3:
    print("usage: %s [options] <name> <type> <port>"%sys.argv[0])
    sys.exit(2)
    
app = QtCore.QCoreApplication(sys.argv)

def callback(announcer):
    print("Registered service:")
    print(" name: \"%s\""%announcer.name())
    print(" domain: \"%s\""%announcer.domain())
    print(" type: \"%s\""%announcer.type())
    print(" status:", announcer.status())

name = args[0]
regtype = args[1]
port = int(args[2])
s1 = DNSServiceAnnouncer(name, regtype, port,
			 txtrec,
			 host, domain,
			 callback=callback)
sys.exit(app.exec_())
