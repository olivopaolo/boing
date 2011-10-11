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
from boing.udp.UdpSocket import UdpSocket, UdpListener, UdpSender, UdpLink

class TestUdpSocket(unittest.TestCase):

    def setUp(self):
        self.data = b"boing-unittest"
    
    def test_udplistener_empty(self):
        s = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        l = UdpListener()
        url = l.getURL()
        s.connect((url.site.host, url.site.port))
        s.send(self.data)
        r = l.receive()
        self.assertEqual(r[0], self.data)
        self.assertEqual(r[1], s.getsockname())

    def test_udplistener(self):
        s = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        l = UdpListener("udp://:7777")
        url = l.getURL()
        s.connect((url.site.host, url.site.port))
        s.send(self.data)
        r = l.receive()
        self.assertEqual(r[0], self.data)
        self.assertEqual(r[1], s.getsockname())

    def test_udplistener_ip6(self):
        s = socket.socket(ip.PF_INET6, socket.SOCK_DGRAM)
        l = UdpListener("udp://[::1]:7777")
        url = l.getURL()
        s.connect((url.site.host, url.site.port))
        s.send(self.data)
        r = l.receive()
        self.assertEqual(r[0], self.data)
        self.assertEqual(r[1], s.getsockname())

    def test_udpsocket(self):
        l = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        l.bind(("",0))
        addr = l.getsockname()[:2]
        s = UdpSocket()
        s.sendTo(self.data, addr)
        r = l.recvfrom(1024)
        self.assertEqual(r[0], self.data)

    def test_udpsocket_ip6(self):
        l = socket.socket(ip.PF_INET6, socket.SOCK_DGRAM)
        l.bind(("::1",0))
        addr = l.getsockname()[:2]
        s = UdpSocket(ip.PF_INET6)
        s.sendTo(self.data, addr)
        r = l.recvfrom(1024)
        self.assertEqual(r[0], self.data)

    def test_udpsender(self):
        l = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        l.bind(("",0))
        addr = l.getsockname()[:2]
        s = UdpSender("udp://%s:%d"%addr)
        url = s.getURL()
        s.send(self.data)
        r = l.recvfrom(1024)
        self.assertEqual(r[0], self.data)
        self.assertEqual(r[1], (url.site.host, url.site.port))

    def test_udpsender_ip6(self):
        l = socket.socket(ip.PF_INET6, socket.SOCK_DGRAM)
        l.bind(("::1",0))
        addr = l.getsockname()[:2]
        s = UdpSender("udp://[%s]:%d"%addr)
        url = s.getURL()
        s.send(self.data)
        r = l.recvfrom(1024)
        self.assertEqual(r[0], self.data)
        self.assertEqual(r[1][:2], (url.site.host, url.site.port))

    def test_udplink(self):
        s = UdpLink("udp://:7777","udp://:7777")
        self.assertEqual(s.send(self.data), len(self.data))
        r = s.receive()
        self.assertEqual(r[0], self.data)

    def test_udplink_ip6(self):
        s = UdpLink("udp://[::1]:7777","udp://[::1]:7777")
        self.assertEqual(s.send(self.data), len(self.data))
        r = s.receive()
        self.assertEqual(r[0], self.data)

# -------------------------------------------------------------------

def suite():
    tests = list(t for t in TestUdpSocket.__dict__ \
                     if t.startswith("test_"))
    return unittest.TestSuite(map(TestUdpSocket, tests))    

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
