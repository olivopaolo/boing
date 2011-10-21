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
import weakref

from PyQt4 import QtCore

from boing import ip
from boing.eventloop.EventLoop import EventLoop
from boing.tcp.EchoServer import EchoServer
from boing.tcp.TcpSocket import TcpSocket, TcpConnection
from boing.url import URL

class TestTcpSocket(QtCore.QObject, unittest.TestCase):

    def __init__(self, *argv, **kwargs):
        QtCore.QObject.__init__(self)
        unittest.TestCase.__init__(self, *argv, **kwargs)

    def setUp(self):
        self.data = b"boing-unittest"
        self.result = ""
        self.timeout = False
    
    def __send_data(self, tid, sock):
        sock.send(self.data)

    def __readdata(self):
        conn = self.sender() 
        self.result += conn.receive()
        EventLoop.stop()

    def __timeout(self, tid):
        self.timeout = True
        EventLoop.stop()

    def test_tcpconnection_ip4(self):
        serv = EchoServer(host="0.0.0.0")
        conn = TcpConnection("tcp://127.0.0.1:%d"%serv.name()[1])
        conn.readyRead.connect(self.__readdata)
        tid_send = EventLoop.after(.1, self.__send_data, conn)
        tid_timeout = EventLoop.after(1, self.__timeout)
        EventLoop.run()
        EventLoop.cancel_timer(tid_send)
        EventLoop.cancel_timer(tid_timeout)
        url = conn.url()
        peerurl = conn.peerUrl()
        self.assertIsInstance(url, URL)
        self.assertEqual(url.scheme, "tcp")
        self.assertEqual(conn.name(), (url.site.host, url.site.port))
        self.assertEqual(conn.peerName(), (peerurl.site.host, peerurl.site.port))
        self.assertEqual(peerurl.site.host, "127.0.0.1")
        self.assertEqual(peerurl.site.port, serv.name()[1])
        self.assertFalse(self.timeout)
        self.assertEqual(self.data, self.result)
        conn.close()

    def test_tcpconnection_ip6(self):
        serv = EchoServer(host="::")
        conn = TcpConnection("tcp://[::1]:%d"%serv.name()[1])
        conn.readyRead.connect(self.__readdata)
        tid_send = EventLoop.after(.1, self.__send_data, conn)
        tid_timeout = EventLoop.after(1, self.__timeout)
        EventLoop.run()
        EventLoop.cancel_timer(tid_send)
        EventLoop.cancel_timer(tid_timeout)
        url = conn.url()
        peerurl = conn.peerUrl()
        self.assertIsInstance(url, URL)
        self.assertEqual(url.scheme, "tcp")
        self.assertEqual(conn.name(), (url.site.host, url.site.port))
        self.assertEqual(conn.peerName(), (peerurl.site.host, peerurl.site.port))
        self.assertEqual(peerurl.site.host, "::1")
        self.assertEqual(peerurl.site.port, serv.name()[1])
        self.assertFalse(self.timeout)
        self.assertEqual(self.data, self.result)
        conn.close()

# -------------------------------------------------------------------

def suite():
    tests = list(t for t in TestTcpSocket.__dict__ \
                     if t.startswith("test_"))
    return unittest.TestSuite(map(TestTcpSocket, tests))    

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
