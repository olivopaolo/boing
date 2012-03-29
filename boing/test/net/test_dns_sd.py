#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# boing/test/dns_sd/test_dns_sd.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import socket
import sys
import unittest
import weakref

from PyQt4 import QtCore

from boing.net.dns_sd.DNSServiceAnnouncer import DNSServiceAnnouncer
from boing.net.dns_sd.DNSServiceBrowser import DNSServiceBrowser

class Testdns_sd(unittest.TestCase):

    def setUp(self):
        self.announcers = []
        self.regtype = "_boing_unittest._tcp."
        self.domain = "local."
        self.host = socket.gethostname()+'.'+self.domain[:-1]
        self.port = 8123
        self.txtrec = {"module":"unittest/dns_sd/", "file":"test_dns_sd.py"}
        self.result = {}
        self.alive = []
        self.complete = False
        self.app = QtCore.QCoreApplication(sys.argv)

    def tearDown(self):
        self.app.exit()
        self.app = None

    def browserEvent(self, event, service):
        if service.name!=self.name: return
        r = self.result.setdefault(service.key(), {})        
        if event=="found":
            self.alive.append(service.key())
            r['name'] = service.name
            r['type'] = service.type+'.'
            r['domain'] = service.domain
            r['interface'] = service.interface
            r['fullname'] = service.fullname()
            # add listener to grab also txtupdate and resolve events
            service.addListener(self.browserEvent)
            service.queryTXTrecord()
            service.resolve()
        elif event=="txtupdate":                
            r['txtrec'] = service.info.get(service.interface, {}).get('txt', {})
        elif event=="resolved":
            r['srv'] = service.info.get(service.interface, {}).get('srv',{})
        elif event=="lost":
            if service.key() in self.alive: 
                self.alive.remove(service.key())
            if len(self.alive)==0:
                self.complete = True
                self.app.quit()

    def test_DNSServiceAnnouncer(self):
        def callback(a, *args, **kwargs):             
            d = self.result.setdefault(a.name(), {})
            d['type'] = a.type() 
            d['domain'] = a.domain() 
            d['status'] = a.status()
            a.__del__()
            if len(self.result)==2:
                self.app.quit()

        name_1 = 'test_1_1'
        self.announcers.append(
            DNSServiceAnnouncer(name=name_1,
                                regtype=self.regtype,
                                port=self.port,
                                callback=callback))
        name_2 = 'test_1_2'
        self.announcers.append(
            DNSServiceAnnouncer(name=name_2,
                                regtype=self.regtype,
                                port=self.port,
                                txtrec=self.txtrec,
                                host=self.host,
                                domain=self.domain, 
                                callback=callback))
        QtCore.QTimer.singleShot(2000, self.app.quit)
        self.app.exec_()
        self.assertEqual(len(self.result), 2)
        d = self.result.get(name_1, None)
        self.assertIsNotNone(d)
        self.assertEqual(d['type'], self.regtype)
        self.assertEqual(d['status'], "noerror")
        d = self.result.get(name_2, None)
        self.assertIsNotNone(d)
        self.assertEqual(d['type'], self.regtype)
        self.assertEqual(d['domain'], self.domain)
        self.assertEqual(d['status'], "noerror")        

    def test_announce_browse_resolve_remove_1(self):
        self.name = 'test_2'
        self.announcers.append(
            DNSServiceAnnouncer(name=self.name, 
                                regtype=self.regtype,
                                port=self.port))
        self.announcers[0].updatetxt(self.txtrec)
        browser = DNSServiceBrowser(self.regtype)
        browser.addListener(self.browserEvent)
        bref = weakref.ref(browser)
        setter = lambda obj, key, value: obj.__setitem__(key, value)
        QtCore.QTimer.singleShot(2000, lambda : setter(self.announcers, 0, None))
        QtCore.QTimer.singleShot(7000, self.app.quit)
        self.app.exec_()
        fullname = self.name+'.'+self.regtype+self.domain
        found = False
        for r in self.result.values():
            if r.get('name') == self.name:
                found = True
                self.assertEqual(r.get('type'), self.regtype)
                self.assertEqual(r.get('txtrec'), self.txtrec)
                self.assertGreaterEqual(r.get('interface'), 0)                
                self.assertEqual(r.get('fullname'), fullname)                
                self.assertEqual(r.get('srv', {}).get('port'), self.port)
        self.assertTrue(found)
        self.assertTrue(self.complete)
        del browser
        self.assertIsNone(bref())

    def test_announce_browse_resolve_remove_2(self):
        self.name = 'test_3'
        self.announcers.append(
            DNSServiceAnnouncer(name=self.name,
                                regtype=self.regtype,
                                port=self.port,
                                txtrec=self.txtrec,
                                host=self.host,
                                domain=self.domain))
        browser = DNSServiceBrowser(self.regtype)
        browser.addListener(self.browserEvent)
        setter = lambda obj, key, value: obj.__setitem__(key, value)
        QtCore.QTimer.singleShot(2000, lambda : setter(self.announcers, 0, None))
        QtCore.QTimer.singleShot(7000, self.app.quit)
        self.app.exec_()
        fullname = self.name+'.'+self.regtype+self.domain
        found = False
        for r in self.result.values():
            if r.get('name') == self.name:
                found = True
                self.assertEqual(r.get('type'), self.regtype)
                self.assertEqual(r.get('domain'), self.domain)
                self.assertEqual(r.get('txtrec'), self.txtrec)
                self.assertGreaterEqual(r.get('interface'), 0)                
                self.assertEqual(r.get('fullname'), fullname)                
                self.assertEqual(r.get('srv', {}).get('port'), self.port)
                self.assertEqual(r.get('srv', {}).get('target'), self.host)
        self.assertTrue(found)
        self.assertTrue(self.complete)

# -------------------------------------------------------------------

def suite():
    tests = (t for t in Testdns_sd.__dict__ if t.startswith("test_"))
    return unittest.TestSuite(map(Testdns_sd, tests))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
