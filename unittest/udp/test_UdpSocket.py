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
import sys

from boing import ip
from boing.udp.UdpSocket import UdpSocket, UdpListener, UdpSender

class TestUdpListener(unittest.TestCase):

    def __init__(self, methodname):
        unittest.TestCase.__init__(self, methodname)
        #self.port = 7777
        #self.lock = UdpListener("udp://0.0.0.0:%d"%self.port, 
        #                        options=("reuse",))
        #self.lock6 = UdpListener("udp://[::]:%d"%self.port, 
        #                         options=("reuse",))

    #def __del__(self):
    #    self.lock.close()
    #    self.lock6.close()
                
    def setUp(self):
        self.data = b"boing-unittest"
        #self.port = self.lock.url().site.port
        #self.lock6 = UdpListener("udp://[::]:%d"%self.port, options=("reuse",))

    #def tearDown(self):
        #self.lock.close()
        #self.lock6.close()

    def test_udplistener_empty_IPv4(self):
        s = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        l = UdpListener(family=ip.PF_INET)
        url = l.url()
        s.connect((socket.gethostname(), url.site.port))
        s.send(self.data)
        data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, s.getsockname())

    def test_udplistener_empty_IPv6(self):
        s = socket.socket(ip.PF_INET6, socket.SOCK_DGRAM)
        l = UdpListener(family=ip.PF_INET6)
        url = l.url()
        s.connect((socket.gethostname(), url.site.port))
        sockname = s.getsockname()
        sockname = (sockname[0].partition("%")[0], sockname[1])
        s.send(self.data)
        data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, sockname)

    def test_udplistener_empty_host(self):
        s = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        l = UdpListener("udp://:0", family=ip.PF_INET)
        url = l.url()
        s.connect((socket.gethostname(), url.site.port))
        s.send(self.data)
        data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, s.getsockname())

    def test_udplistener_empty_host_IPv6(self):
        s = socket.socket(ip.PF_INET6, socket.SOCK_DGRAM)
        l = UdpListener("udp://:0", family=ip.PF_INET6)
        url = l.url()
        s.connect((socket.gethostname(), url.site.port))
        sockname = s.getsockname()
        sockname = (sockname[0].partition("%")[0], sockname[1])
        s.send(self.data)
        data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, sockname)

    def test_udplistener_any_ip4(self):
        s = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        l = UdpListener("udp://0.0.0.0:0")
        url = l.url()
        s.connect((socket.gethostname(), url.site.port))
        s.send(self.data)
        data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, s.getsockname())

    def test_udplistener_any_ip6(self):
        s = socket.socket(ip.PF_INET6, socket.SOCK_DGRAM)
        l = UdpListener("udp://[::]:0")
        url = l.url()
        s.connect((socket.gethostname(), url.site.port))
        sockname = s.getsockname()
        sockname = (sockname[0].partition("%")[0], sockname[1])
        s.send(self.data)
        data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, sockname)

    def test_udplistener_localhost_IPv4(self):
        s = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        l = UdpListener("udp://localhost:0", ip.PF_INET)
        url = l.url()
        s.connect((url.site.host, url.site.port))
        s.send(self.data)
        data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, s.getsockname())

    def test_udplistener_localhost_IPv6(self):
        s = socket.socket(ip.PF_INET6, socket.SOCK_DGRAM)
        l = UdpListener("udp://localhost:0", ip.PF_INET6)
        url = l.url()
        s.connect((url.site.host, url.site.port))
        s.send(self.data)
        data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, s.getsockname()[:2])

    def test_udplistener_loopback_IPv4(self):
        s = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        l = UdpListener("udp://127.0.0.1:0")
        url = l.url()
        s.connect((url.site.host, url.site.port))
        s.send(self.data)
        data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, s.getsockname())

    def test_udplistener_loopback_IPv6(self):
        s = socket.socket(ip.PF_INET6, socket.SOCK_DGRAM)
        l = UdpListener("udp://[::1]:0")
        url = l.url()
        s.connect((url.site.host, url.site.port))
        s.send(self.data)
        data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, s.getsockname()[:2])

    def test_udplistener_hostname_IPv4(self):
        s = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        hostname = socket.gethostname()
        l = UdpListener("udp://%s:0"%hostname, ip.PF_INET)
        url = l.url()
        s.connect((url.site.host, url.site.port))
        sockname = s.getsockname()
        s.send(self.data)
        data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, sockname)

    def test_udplistener_hostname_IPv6(self):
        s = socket.socket(ip.PF_INET6, socket.SOCK_DGRAM)
        hostname = socket.gethostname()
        l = UdpListener("udp://%s:0"%hostname, ip.PF_INET6)
        url = l.url()
        s.connect((url.site.host, url.site.port))
        sockname = s.getsockname()[:2]
        sockname = (sockname[0].partition("%")[0], sockname[1])
        s.send(self.data)
        data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, sockname)

    # ---------------------------------------------------------------------
    # "reuse" option cases

    def test_udplistener_empty_host_reuse(self):
        lock = UdpListener("udp://0.0.0.0:0", options=("reuse",))
        port = lock.name()[1]
        s = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        self.assertRaises(Exception, UdpListener, 
                          "udp://:%d"%port, family=ip.PF_INET)
        l = UdpListener("udp://:%d"%port,
                        family=ip.PF_INET, options=("reuse",))
        url = l.url()
        self.assertEqual(url.site.port, port)
        s.connect((socket.gethostname(), port))
        s.send(self.data)
        if sys.platform=="win32": data, source = lock.receiveFrom()
        else: data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, s.getsockname())
        lock.close()

    def test_udplistener_empty_host_IPv6_reuse(self):
        lock = UdpListener("udp://[::]:0", options=("reuse",))
        port = lock.name()[1]
        s = socket.socket(ip.PF_INET6, socket.SOCK_DGRAM)
        self.assertRaises(Exception, UdpListener, 
                          "udp://:%d"%port, family=ip.PF_INET6)
        l = UdpListener("udp://:%d"%port,
                        family=ip.PF_INET6, options=("reuse",))
        url = l.url()
        self.assertEqual(url.site.port, port)
        s.connect((socket.gethostname(), url.site.port))
        sockname = s.getsockname()
        sockname = (sockname[0].partition("%")[0], sockname[1])
        s.send(self.data)
        if sys.platform=="win32":data, source = lock.receiveFrom()
        else: data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, sockname)
        lock.close()

    def test_udplistener_any_ip4_reuse(self):
        lock = UdpListener("udp://0.0.0.0:0", options=("reuse",))
        port = lock.name()[1]
        s = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        self.assertRaises(Exception, UdpListener, 
                          "udp://0.0.0.0:%d"%port)
        l = UdpListener("udp://0.0.0.0:%d"%port,("reuse",), 
                        options=("reuse",))
        url = l.url()
        self.assertEqual(url.site.port, port)
        s.connect((socket.gethostname(), url.site.port))
        s.send(self.data)
        if sys.platform=="win32":data, source = lock.receiveFrom()
        else: data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, s.getsockname())
        lock.close()

    def test_udplistener_any_ip6_reuse(self):
        lock = UdpListener("udp://[::]:0", options=("reuse",))
        port = lock.name()[1]
        s = socket.socket(ip.PF_INET6, socket.SOCK_DGRAM)
        self.assertRaises(Exception, UdpListener, 
                          "udp://[::]:%d"%port)
        l = UdpListener("udp://[::]:%d"%port,("reuse",), 
                        options=("reuse",))
        url = l.url()
        self.assertEqual(url.site.port, port)
        s.connect((socket.gethostname(), url.site.port))
        sockname = s.getsockname()
        sockname = (sockname[0].partition("%")[0], sockname[1])
        s.send(self.data)
        if sys.platform=="win32":data, source = lock.receiveFrom()
        else: data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, sockname)
        lock.close()

    def test_udplistener_localhost_IPv4_reuse(self):
        lock = UdpListener("udp://localhost:0", ip.PF_INET, ("reuse",))
        port = lock.name()[1]
        s = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        self.assertRaises(Exception, UdpListener, 
                          "udp://localhost:%d"%port, ip.PF_INET)
        l = UdpListener("udp://localhost:%d"%port,
                        ip.PF_INET,("reuse",))
        url = l.url()
        self.assertEqual(url.site.port, port)
        s.connect((url.site.host, url.site.port))
        s.send(self.data)
        if sys.platform=="win32": data, source = lock.receiveFrom()
        else: data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, s.getsockname())
        lock.close()

    def test_udplistener_localhost_IPv6_reuse(self):
        lock = UdpListener("udp://localhost:0", ip.PF_INET6, ("reuse",))
        port = lock.name()[1]
        s = socket.socket(ip.PF_INET6, socket.SOCK_DGRAM)
        self.assertRaises(Exception, UdpListener, 
                          "udp://localhost:%d"%port, ip.PF_INET6)
        l = UdpListener("udp://localhost:%d"%port,
                        ip.PF_INET6, ("reuse",))
        url = l.url()
        self.assertEqual(url.site.port, port)
        s.connect((url.site.host, url.site.port))
        s.send(self.data)
        if sys.platform=="win32": data, source = lock.receiveFrom()
        else: data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, s.getsockname()[:2])
        lock.close()

    def test_udplistener_loopback_IPv4_reuse(self):
        lock = UdpListener("udp://127.0.0.1:0", options=("reuse",))
        port = lock.name()[1]
        s = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        self.assertRaises(Exception, UdpListener, 
                          "udp://127.0.0.1:%d"%port)
        l = UdpListener("udp://127.0.0.1:%d"%port, options=("reuse",))
        url = l.url()
        self.assertEqual(url.site.port, port)
        s.connect((url.site.host, url.site.port))
        s.send(self.data)
        if sys.platform=="win32":data, source = lock.receiveFrom()
        else: data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, s.getsockname())
        lock.close()

    def test_udplistener_loopback_IPv6_reuse(self):
        lock = UdpListener("udp://[::1]:0", options=("reuse",))
        port = lock.name()[1]
        s = socket.socket(ip.PF_INET6, socket.SOCK_DGRAM)
        self.assertRaises(Exception, UdpListener, 
                          "udp://[::1]:%d"%port)
        l = UdpListener("udp://[::1]:%d"%port, options=("reuse",))
        url = l.url()
        self.assertEqual(url.site.port, port)
        s.connect((url.site.host, url.site.port))
        s.send(self.data)
        if sys.platform=="win32": data, source = lock.receiveFrom()
        else: data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, s.getsockname()[:2])
        lock.close()

    def test_udplistener_hostname_IPv4_reuse(self):
        hostname = socket.gethostname()
        lock = UdpListener("udp://%s:0"%hostname, ip.PF_INET, ("reuse",))
        port = lock.name()[1]
        s = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        self.assertRaises(Exception, UdpListener, 
                          "udp://%s:%d"%(hostname, port), ip.PF_INET)
        l = UdpListener("udp://%s:%d"%(hostname, port),
                        ip.PF_INET, ("reuse",))
        url = l.url()
        self.assertEqual(url.site.port, port)
        s.connect((url.site.host, url.site.port))
        sockname = s.getsockname()
        s.send(self.data)
        if sys.platform=="win32":data, source = lock.receiveFrom()
        else: data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, sockname)
        lock.close()

    def test_udplistener_hostname_IPv6_reuse(self):
        hostname = socket.gethostname()
        lock = UdpListener("udp://%s:0"%hostname, ip.PF_INET6, ("reuse",))
        port = lock.name()[1]
        s = socket.socket(ip.PF_INET6, socket.SOCK_DGRAM)
        self.assertRaises(Exception, UdpListener, 
                          "udp://%s:%d"%(hostname, port), ip.PF_INET6)
        l = UdpListener("udp://%s:%d"%(hostname, port),
                        ip.PF_INET6, ("reuse",))
        url = l.url()
        self.assertEqual(url.site.port, port)
        s.connect((url.site.host, url.site.port))
        sockname = s.getsockname()[:2]
        sockname = (sockname[0].partition("%")[0], sockname[1])
        s.send(self.data)
        if sys.platform=="win32":data, source = lock.receiveFrom()
        else: data, source = l.receiveFrom()
        self.assertEqual(data, self.data)
        self.assertEqual(source, sockname)
        lock.close()


class TestUdpSocket(unittest.TestCase):

    def setUp(self):
        self.data = b"boing-unittest"    

    def test_udpsocket_loopback_IPv4(self):
        l = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        l.bind(("127.0.0.1",0))
        addr, port = l.getsockname()[:2]
        s = UdpSocket()
        n = s.sendTo(self.data, "127.0.0.1", int(port))
        self.assertEqual(n, len(self.data))
        data, source = l.recvfrom(1024)
        self.assertEqual(data, self.data)

    def test_udpsocket_loopback_IPv6(self):
        l = socket.socket(ip.PF_INET6, socket.SOCK_DGRAM)
        l.bind(("::1",0))
        addr, port = l.getsockname()[:2]
        s = UdpSocket()
        n = s.sendTo(self.data, "::1", int(port))
        self.assertEqual(n, len(self.data))
        data, source = l.recvfrom(1024)
        self.assertEqual(data, self.data)

    def test_udpsocket_localhost_IPv4(self):
        l = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        l.bind(("localhost",0))
        addr, port = l.getsockname()[:2]
        s = UdpSocket()
        n = s.sendTo(self.data, "localhost", int(port),
                     ip.PF_INET)
        self.assertEqual(n, len(self.data))
        data, source = l.recvfrom(1024)
        self.assertEqual(data, self.data)

    def test_udpsocket_localhost_IPv6(self):
        l = socket.socket(ip.PF_INET6, socket.SOCK_DGRAM)
        l.bind(("localhost",0))
        addr, port = l.getsockname()[:2]
        s = UdpSocket()
        n = s.sendTo(self.data, "localhost", int(port),
                     ip.PF_INET6)
        self.assertEqual(n, len(self.data))
        data, source = l.recvfrom(1024)
        self.assertEqual(data, self.data)

    def test_udpsocket_hostname_IPv4(self):
        l = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        l.bind((socket.gethostname(),0))
        addr, port = l.getsockname()[:2]
        s = UdpSocket()
        n = s.sendTo(self.data, socket.gethostname(), int(port),
                     ip.PF_INET)
        self.assertEqual(n, len(self.data))
        data, source = l.recvfrom(1024)
        self.assertEqual(data, self.data)

    def test_udpsocket_hostname_IPv6(self):
        l = socket.socket(ip.PF_INET6, socket.SOCK_DGRAM)
        l.bind((socket.gethostname(),0))
        addr, port = l.getsockname()[:2]
        s = UdpSocket()
        n = s.sendTo(self.data, socket.gethostname(), int(port),
                     ip.PF_INET6)
        self.assertEqual(n, len(self.data))
        data, source = l.recvfrom(1024)
        self.assertEqual(data, self.data)

    def test_udpsocket_broadcast_IPv4(self):
        l = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        l.bind(("0.0.0.0",0))
        addr, port = l.getsockname()[:2]
        s = UdpSocket()
        n = s.sendTo(self.data, "255.255.255.255", int(port))
        self.assertEqual(n, len(self.data))
        data, source = l.recvfrom(1024)
        self.assertEqual(data, self.data)


class TestUdpSender(unittest.TestCase):

    def setUp(self):
        self.data = b"boing-unittest"    

    def test_udpsender_loopback_IPv4(self):
        l = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        l.bind(("127.0.0.1",0))
        addr = l.getsockname()[:2]
        s = UdpSender("udp://%s:%d"%addr)
        url = s.url()
        peerurl = s.peerUrl()
        self.assertEqual((peerurl.site.host, peerurl.site.port), 
                         l.getsockname()[:2])        
        n = s.send(self.data)
        self.assertEqual(n, len(self.data))
        data, source = l.recvfrom(1024)
        self.assertEqual(data, self.data)
        self.assertEqual(source, (url.site.host, url.site.port))

    def test_udpsender_loopback_IPv6(self):
        l = socket.socket(ip.PF_INET6, socket.SOCK_DGRAM)
        l.bind(("::1",0))
        addr = l.getsockname()[:2]
        s = UdpSender("udp://[%s]:%d"%addr)
        url = s.url()
        peerurl = s.peerUrl()
        self.assertEqual((peerurl.site.host, peerurl.site.port), 
                         l.getsockname()[:2])        
        n = s.send(self.data)
        self.assertEqual(n, len(self.data))
        data, source = l.recvfrom(1024)
        self.assertEqual(data, self.data)
        self.assertEqual(source[:2], (url.site.host, url.site.port))

    def test_udpsender_localhost_IPv4(self):
        l = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        l.bind(("localhost",0))
        addr, port = l.getsockname()[:2]
        s = UdpSender("udp://localhost:%d"%port, ip.PF_INET)
        url = s.url()
        peerurl = s.peerUrl()
        self.assertEqual((peerurl.site.host, peerurl.site.port), 
                         l.getsockname()[:2])        
        n = s.send(self.data)
        self.assertEqual(n, len(self.data))
        data, source = l.recvfrom(1024)
        self.assertEqual(data, self.data)
        self.assertEqual(source, (url.site.host, url.site.port))

    def test_udpsender_localhost_IPv6(self):
        l = socket.socket(ip.PF_INET6, socket.SOCK_DGRAM)
        l.bind(("localhost",0))
        addr, port = l.getsockname()[:2]
        s = UdpSender("udp://localhost:%d"%port, ip.PF_INET6)
        url = s.url()
        peerurl = s.peerUrl()
        self.assertEqual((peerurl.site.host, peerurl.site.port), 
                         l.getsockname()[:2])        
        n = s.send(self.data)
        self.assertEqual(n, len(self.data))
        data, source = l.recvfrom(1024)
        self.assertEqual(data, self.data)
        self.assertEqual(source[:2], (url.site.host, url.site.port))

    def test_udpsender_hostname_IPv4(self):
        l = socket.socket(ip.PF_INET, socket.SOCK_DGRAM)
        l.bind((socket.gethostname(),0))
        addr, port = l.getsockname()[:2]
        s = UdpSender("udp://%s:%d"%(socket.gethostname(),port), 
                      ip.PF_INET)
        url = s.url()
        peerurl = s.peerUrl()
        self.assertEqual((peerurl.site.host, peerurl.site.port), 
                         l.getsockname()[:2])        
        n = s.send(self.data)
        self.assertEqual(n, len(self.data))
        data, source = l.recvfrom(1024)
        self.assertEqual(data, self.data)
        self.assertEqual(source, (url.site.host, url.site.port))

    def test_udpsender_hostname_IPv6(self):
        l = socket.socket(ip.PF_INET6, socket.SOCK_DGRAM)
        l.bind((socket.gethostname(),0))
        addr, port = l.getsockname()[:2]
        s = UdpSender("udp://%s:%d"%(socket.gethostname(),port), 
                      ip.PF_INET6)
        url = s.url()
        peerurl = s.peerUrl()
        sockname = l.getsockname()[:2]
        sockname = (sockname[0].partition("%")[0], sockname[1])
        self.assertEqual((peerurl.site.host, peerurl.site.port), 
                         sockname)        
        n = s.send(self.data)
        self.assertEqual(n, len(self.data))
        data, source = l.recvfrom(1024)
        source = (source[0].partition("%")[0], source[1])
        self.assertEqual(data, self.data)
        self.assertEqual(source, (url.site.host, url.site.port))

# -------------------------------------------------------------------

def suite():
    sockettests = list(t for t in TestUdpSocket.__dict__ \
                         if t.startswith("test_"))
    sendertests = list(t for t in TestUdpSender.__dict__ \
                         if t.startswith("test_"))
    listenertests = list(t for t in TestUdpListener.__dict__ \
                           if t.startswith("test_"))
    return unittest.TestSuite(list(map(TestUdpSocket, sockettests))+
                              list(map(TestUdpSender, sendertests))+
                              list(map(TestUdpListener, listenertests)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
