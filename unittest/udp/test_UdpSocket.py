#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# unittest/udp/test_UdpSocket.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import unittest
import socket

from boing import ip
from boing.udp.UdpSocket import UdpSocket, UdpListener, UdpSender

class TestUdpListener(unittest.TestCase):

    def __init__(self, methodname):
        # This enables to parametrize test cases.
        methodname, self.reuse = methodname
        super().__init__(methodname)
        if self.reuse:
            self.options=("reuse",)
            self.port = 78971
            self.lockers = (UdpListener("udp://0.0.0.0:%d"%self.port, 
                                        self.options),
                            UdpListener("udp://[::]:%d"%self.port, 
                                        self.options))
        else:
            self.options=tuple()
            self.port = 0

    def __del__(self):
        super().__del__()
        if self.reuse: 
            for socket in self.lockers:
                socket.close()

    def setUp(self):
        self.data = b"boing-unittest"

    def test_udplistener_empty(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        l = UdpListener(options=self.options)
        url = l.url()
        s.connect((url.site.host, url.site.port))
        s.send(self.data)
        r = l.receiveFrom()
        self.assertEqual(r[0], self.data)
        self.assertEqual(r[1], s.getsockname())

    def test_udplistener_empty_host(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if self.reuse: self.assertRaises(Exception, 
                                         UdpListener, 
                                         "udp://:%d"%self.port)
        l = UdpListener("udp://:%d"%self.port,self.options)
        url = l.url()
        s.connect((url.site.host, url.site.port))
        s.send(self.data)
        r = l.receiveFrom()
        self.assertEqual(r[0], self.data)
        self.assertEqual(r[1], s.getsockname()[:2])

    def test_udplistener_any_ip4(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if self.reuse: self.assertRaises(Exception, 
                                         UdpListener, 
                                         "udp://0.0.0.0:%d"%self.port)
        l = UdpListener("udp://0.0.0.0:%d"%self.port,self.options)
        url = l.url()
        s.connect((url.site.host, url.site.port))
        s.send(self.data)
        r = l.receiveFrom()
        self.assertEqual(r[0], self.data)
        self.assertEqual(r[1], s.getsockname())

    def test_udplistener_any_ip6(self):
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        if self.reuse: self.assertRaises(Exception, 
                                         UdpListener, 
                                         "udp://[::]:%d"%self.port)
        l = UdpListener("udp://[::]:%d"%self.port,self.options)
        url = l.url()
        s.connect((url.site.host, url.site.port))
        s.send(self.data)
        r = l.receiveFrom()
        self.assertEqual(r[0], self.data)
        self.assertEqual(r[1], s.getsockname()[:2])

    def test_udplistener_localhost(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if self.reuse: self.assertRaises(Exception, 
                                         UdpListener, 
                                         "udp://localhost:%d"%self.port)
        l = UdpListener("udp://localhost:%d"%self.port,self.options)
        url = l.url()
        s.connect((url.site.host, url.site.port))
        s.send(self.data)
        r = l.receiveFrom()
        self.assertEqual(r[0], self.data)
        self.assertEqual(r[1], s.getsockname())

    def test_udplistener_localhost_ip6(self):
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        if self.reuse: 
            self.assertRaises(Exception, UdpListener, 
                              "udp://[::1]:%d"%self.port)
        l = UdpListener("udp://[::1]:%d"%self.port,self.options)
        url = l.url()
        s.connect((url.site.host, url.site.port))
        s.send(self.data)
        r = l.receiveFrom()
        self.assertEqual(r[0], self.data)
        self.assertEqual(r[1], s.getsockname()[:2])

    def test_udplistener_hostname(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        hostname = socket.gethostname()
        if self.reuse: 
            self.assertRaises(Exception, UdpListener, 
                              "udp://%s:%d"%(hostname, self.port))
        l = UdpListener("udp://%s:%d"%(hostname, self.port),self.options)
        url = l.url()
        s.connect((url.site.host, url.site.port))
        s.send(self.data)
        r = l.receiveFrom()
        self.assertEqual(r[0], self.data)
        self.assertEqual(r[1], s.getsockname())


class TestUdpSocket(unittest.TestCase):

    def setUp(self):
        self.data = b"boing-unittest"    

    def test_udpsocket(self):
        l = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        l.bind(("127.0.0.1",0))
        addr, port = l.getsockname()[:2]
        s = UdpSocket()
        n = s.sendTo(self.data, addr, int(port))
        self.assertEqual(n, len(self.data))
        r = l.recvfrom(1024)
        self.assertEqual(r[0], self.data)

    def test_udpsocket_broadcast(self):
        l = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        l.bind(("0.0.0.0",0))
        addr, port = l.getsockname()[:2]
        s = UdpSocket()
        n = s.sendTo(self.data, "255.255.255.255", int(port))
        self.assertEqual(n, len(self.data))
        r = l.recvfrom(1024)
        self.assertEqual(r[0], self.data)

    def test_udpsocket_ip6(self):
        l = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        l.bind(("::1",0))
        addr, port = l.getsockname()[:2]
        s = UdpSocket()
        n = s.sendTo(self.data, addr, int(port))
        self.assertEqual(n, len(self.data))
        r = l.recvfrom(1024)
        self.assertEqual(r[0], self.data)

    def test_udpsender(self):
        l = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        l.bind(("127.0.0.1",0))
        addr = l.getsockname()[:2]
        s = UdpSender("udp://%s:%d"%addr)
        url = s.url()
        peerurl = s.peerUrl()
        self.assertEqual((peerurl.site.host, peerurl.site.port), 
                         l.getsockname()[:2])        
        n = s.send(self.data)
        self.assertEqual(n, len(self.data))
        r = l.recvfrom(1024)
        self.assertEqual(r[0], self.data)
        self.assertEqual(r[1], (url.site.host, url.site.port))

    def test_udpsender_localhost(self):
        l = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        l.bind(("127.0.0.1",0))
        addr, port = l.getsockname()[:2]
        s = UdpSender("udp://localhost:%d"%port)
        url = s.url()
        peerurl = s.peerUrl()
        self.assertEqual((peerurl.site.host, peerurl.site.port), 
                         l.getsockname()[:2])        
        n = s.send(self.data)
        self.assertEqual(n, len(self.data))
        r = l.recvfrom(1024)
        self.assertEqual(r[0], self.data)
        self.assertEqual(r[1], (url.site.host, url.site.port))

    def test_udpsender_hostname(self):
        l = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        l.bind((socket.gethostname(),0))
        addr, port = l.getsockname()[:2]
        s = UdpSender("udp://%s:%d"%(socket.gethostname(),port))
        url = s.url()
        peerurl = s.peerUrl()
        self.assertEqual((peerurl.site.host, peerurl.site.port), 
                         l.getsockname()[:2])        
        n = s.send(self.data)
        self.assertEqual(n, len(self.data))
        r = l.recvfrom(1024)
        self.assertEqual(r[0], self.data)
        self.assertEqual(r[1], (url.site.host, url.site.port))

    def test_udpsender_ip6(self):
        l = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        l.bind(("::1",0))
        addr = l.getsockname()[:2]
        s = UdpSender("udp://[%s]:%d"%addr)
        url = s.url()
        peerurl = s.peerUrl()
        self.assertEqual((peerurl.site.host, peerurl.site.port), 
                         l.getsockname()[:2])        
        n = s.send(self.data)
        self.assertEqual(n, len(self.data))
        r = l.recvfrom(1024)
        self.assertEqual(r[0], self.data)
        self.assertEqual(r[1][:2], (url.site.host, url.site.port))

# -------------------------------------------------------------------

def suite():
    sockettests = list(t for t in TestUdpSocket.__dict__ \
                         if t.startswith("test_"))
    listenertests = list((t,False) for t in TestUdpListener.__dict__ \
                                   if t.startswith("test_"))
    listenertests += list((t,True) for t in TestUdpListener.__dict__ \
                                   if t.startswith("test_"))
    return unittest.TestSuite(list(map(TestUdpSocket, sockettests))+
                              list(map(TestUdpListener, listenertests)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
