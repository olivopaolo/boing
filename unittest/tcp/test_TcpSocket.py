#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# unittest/udp/test_TcpSocket.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import unittest
import socket as _socket

from boing import ip
from boing.eventloop.EventLoop import EventLoop
from boing.tcp.EchoServer import EchoServer
from boing.tcp.TcpSocket import TcpSocket, TcpConnection
from boing.tcp.TcpServer import TcpServer
from boing.url import URL

class TestTcpSocket(unittest.TestCase):

    def __socket_listener(self, did, client):
        self.result = client.receive()
        EventLoop.stop()

    def __send_data(self, tid, sock):
        sock.send(self.data)

    def __timeout(self, tid):
        self.timeout = True
        EventLoop.stop()

    def setUp(self):
        self.data = b"boing-unittest"
        self.result = None
        self.timeout = False
    
    def test_tcpsocket_ip4(self):
        s = TcpSocket(ip.PF_INET)
        self.assertRaises(Exception, s.send, self.data)
        url = s.url()
        self.assertIsInstance(url, URL)
        self.assertEqual(s.name(), (url.site.host, url.site.port))
        self.assertIsInstance(s.socket(), _socket.socket)
        self.assertIsNotNone(s.fileno())
        s.close()

    def test_tcpsocket_ip6(self):
        s = TcpSocket(ip.PF_INET6)
        self.assertRaises(Exception, s.send, self.data)
        url = s.url()        
        self.assertIsInstance(url, URL)
        self.assertEqual(s.name()[:2], (url.site.host, url.site.port))
        self.assertIsInstance(s.socket(), _socket.socket)
        self.assertIsNotNone(s.fileno())
        s.close()

    def test_tcpserver_ip4(self):
        s = TcpServer(family=ip.PF_INET)
        url = s.url()
        self.assertIsInstance(url, URL)
        self.assertEqual(s.name(), (url.site.host, url.site.port))
        self.assertIsNotNone(s.fileno())
        self.assertIsInstance(s.socket(), _socket.socket)

    def test_tcpserver_ip6(self):
        s = TcpServer(host="::1", family=ip.PF_INET6)
        url = s.url()        
        self.assertIsInstance(url, URL)
        self.assertEqual(s.name()[:2], (url.site.host, url.site.port))
        self.assertIsNotNone(s.fileno())
        self.assertIsInstance(s.socket(), _socket.socket)

    def test_tcpconnection_ip4(self):
        serv = EchoServer(port=0, host="", family=ip.PF_INET)
        s = TcpConnection("tcp://%s:%d"%serv.name(), ("autoclose",))
        self.assertEqual(serv.name(), s.peername())
        did_client = EventLoop.if_readable(s, self.__socket_listener, s)
        tid_send = EventLoop.after(.01, self.__send_data, s)
        tid_timeout = EventLoop.after(1, self.__timeout)
        EventLoop.run()
        EventLoop.cancel_timer(tid_send)
        EventLoop.cancel_timer(tid_timeout)
        EventLoop.cancel_fdhandler(did_client)
        self.assertFalse(self.timeout)
        self.assertEqual(self.data, self.result)

    def test_tcpconnection_ip6(self):
        serv = EchoServer(port=0, host="::1", family=ip.PF_INET6)
        s = TcpConnection("tcp://[%s]:%d"%serv.name()[:2], ("autoclose",))
        self.assertEqual(serv.name(), s.peername())
        did_client = EventLoop.if_readable(s, self.__socket_listener, s)
        tid_send = EventLoop.after(.01, self.__send_data, s)
        tid_timeout = EventLoop.after(1, self.__timeout)
        EventLoop.run()
        EventLoop.cancel_timer(tid_send)
        EventLoop.cancel_timer(tid_timeout)
        EventLoop.cancel_fdhandler(did_client)
        self.assertFalse(self.timeout)
        self.assertEqual(self.data, self.result)

# -------------------------------------------------------------------

def suite():
    tests = list(t for t in TestTcpSocket.__dict__ \
                     if t.startswith("test_"))
    return unittest.TestSuite(map(TestTcpSocket, tests))    

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
