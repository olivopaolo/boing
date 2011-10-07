# -*- coding: utf-8 -*-
#
# unittest/dns_sd/test_dns_sd.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import socket
import unittest

from boing.dns_sd.DNSServiceAnnouncer import DNSServiceAnnouncer
from boing.dns_sd.DNSServiceBrowser import DNSServiceBrowser
from boing.eventloop.EventLoop import EventLoop

class test_dns_sd(unittest.TestCase):

    def setUp(self):
        self.regtype = "_boing_unittest._tcp."
        self.domain = "local."
        self.host = socket.gethostname()+'.'+self.domain[:-1]
        self.port = 8123
        self.txtrec = {"module":"unittest/dns_sd/", "file":"test_dns_sd.py"}
        self.timeout = False
        self.result = {}
        self.alive = []
        self.tid = EventLoop.after(10, self.timeoutEvent)

    def tearDown(self):
        EventLoop.cancel_timer(self.tid)        

    def timeoutEvent(self, *args, **kwargs):
        self.timeout = True
        EventLoop.stop()

    def unallocate(self, tid, announcer, *args, **kwargs):
        announcer.__del__()

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
                EventLoop.stop()

    def test_DNSServiceAnnouncer(self):
        def callback(a, *args, **kwargs):             
            d = self.result.setdefault(a.name(), {})
            d['type'] = a.type() 
            d['domain'] = a.domain() 
            d['status'] = a.status()
            a.__del__()
            if len(self.result)==2:
                EventLoop.stop()

        name_1 = 'test_1_1'
        announcer_1 = DNSServiceAnnouncer(name=name_1,
                                          regtype=self.regtype,
                                          port=self.port,
                                          callback=callback)
        name_2 = 'test_1_2'
        announcer_2 = DNSServiceAnnouncer(name=name_2,
                                          regtype=self.regtype,
                                          port=self.port,
                                          txtrec=self.txtrec,
                                          host=self.host,
                                          domain=self.domain, 
                                          callback=callback)
        EventLoop.run()
        self.assertFalse(self.timeout)
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
        announcer = DNSServiceAnnouncer(name=self.name, 
                                        regtype=self.regtype,
                                        port=self.port)
        browser = DNSServiceBrowser(self.regtype)
        browser.addListener(self.browserEvent)
        tid_2 = EventLoop.after(3, self.unallocate, announcer)
        announcer.updatetxt(self.txtrec)
        EventLoop.run()
        EventLoop.cancel_timer(tid_2)
        self.assertFalse(self.timeout)
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

    def test_announce_browse_resolve_remove_2(self):
        self.name = 'test_3'
        announcer = DNSServiceAnnouncer(name=self.name,
                                        regtype=self.regtype,
                                        port=self.port,
                                        txtrec=self.txtrec,
                                        host=self.host,
                                        domain=self.domain)
        browser = DNSServiceBrowser(self.regtype)
        browser.addListener(self.browserEvent)
        tid_2 = EventLoop.after(3, self.unallocate, announcer)
        EventLoop.run()
        EventLoop.cancel_timer(tid_2)        
        self.assertFalse(self.timeout)
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

# -------------------------------------------------------------------

def suite():
    tests = list(t for t in dir(test_dns_sd) if t.startswith("test_"))
    return unittest.TestSuite(list(map(test_dns_sd, tests)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
