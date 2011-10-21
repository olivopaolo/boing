#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# unittest/udp/test_TcpServer.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import unittest
import socket as _socket
import weakref

from PyQt4 import QtCore
from PyQt4.QtNetwork import QAbstractSocket

from boing import ip
from boing.eventloop.EventLoop import EventLoop
from boing.tcp.TcpSocket import TcpSocket
from boing.tcp.TcpServer import TcpServer
from boing.url import URL

class TestTcpServer(QtCore.QObject, unittest.TestCase):
    
    def __init__(self, methodname):
        # This enables to parametrize test cases.
        method, self.options = methodname
        QtCore.QObject.__init__(self)
        unittest.TestCase.__init__(self, method)

    def setUp(self):
        self.connections = []
        self.data = b"boing-unittest"
        self.result = ""
        self.timeout = False

    def __timeout(self, tid):
        self.timeout = True
        EventLoop.stop()

    def __readdata(self):
        conn = self.sender() 
        self.result += conn.receive()
        EventLoop.stop()

    def __newconnection(self):
        server = self.sender()
        conn = server.nextPendingConnection()
        conn.readyRead.connect(self.__readdata)
        self.connections.append(conn)

    def tryConnectToServer(self, server):
        s = _socket.socket(server.family(), _socket.SOCK_STREAM)
        s.connect(server.name())
        s.send(self.data)
        tid_timeout = EventLoop.after(1, self.__timeout)
        EventLoop.run()
        sockname = s.getsockname()[:2]
        s.close()
        EventLoop.cancel_timer(tid_timeout)
        self.assertFalse(self.timeout)
        self.assertEqual(len(self.connections), 1)        
        conn = self.connections[0]
        self.assertIsInstance(conn, TcpSocket)
        self.assertEqual(conn.state(), QAbstractSocket.ConnectedState)
        self.assertEqual(conn.peerName(), sockname)
        conn.close()
        self.assertEqual(self.result, self.data)
        self.connections = None

    def test_tcpserver_empty(self):
        s = TcpServer(options=self.options)
        s.newConnection.connect(self.__newconnection)
        ref = weakref.ref(s)
        url = s.url()
        self.assertIsInstance(url, URL)
        self.assertEqual(url.scheme, "tcp")
        self.assertEqual(s.name(), (url.site.host, url.site.port))
        self.assertEqual(s.family(), ip.PF_INET)
        self.tryConnectToServer(s)
        del s
        self.assertIsNone(ref())

    def test_tcpserver_localhost(self):
        s = TcpServer(addr="localhost", options=self.options)
        s.newConnection.connect(self.__newconnection)
        ref = weakref.ref(s)
        url = s.url()
        self.assertIsInstance(url, URL)
        self.assertEqual(url.scheme, "tcp")
        self.assertEqual(url.site.host, "127.0.0.1")
        self.assertIsInstance(url.site.port, int)
        self.assertEqual(s.name(), (url.site.host, url.site.port))
        self.assertEqual(s.family(), ip.PF_INET)
        self.tryConnectToServer(s)
        del s
        self.assertIsNone(ref())

    def test_tcpserver_localhost_IPv6(self):
        s = TcpServer(addr="::1", options=self.options)
        s.newConnection.connect(self.__newconnection)
        ref = weakref.ref(s)
        url = s.url()
        self.assertIsInstance(url, URL)
        self.assertEqual(url.scheme, "tcp")
        self.assertEqual(url.site.host, "::1")
        self.assertIsInstance(url.site.port, int)
        self.assertEqual(s.name(), (url.site.host, url.site.port))
        self.assertEqual(s.family(), ip.PF_INET6)
        self.tryConnectToServer(s)
        del s
        self.assertIsNone(ref())

    def test_tcpserver_any(self):
        s = TcpServer(addr="0.0.0.0", options=self.options)
        s.newConnection.connect(self.__newconnection)
        ref = weakref.ref(s)
        url = s.url()        
        self.assertIsInstance(url, URL)
        self.assertEqual(url.scheme, "tcp")
        self.assertEqual(url.site.host, "0.0.0.0")
        self.assertEqual(s.name(), (url.site.host, url.site.port))
        self.assertEqual(s.family(), ip.PF_INET)
        self.tryConnectToServer(s)
        del s
        self.assertIsNone(ref())

    def test_tcpserver_any_IPv6(self):
        s = TcpServer(addr="::", options=self.options)
        s.newConnection.connect(self.__newconnection)
        ref = weakref.ref(s)
        url = s.url()        
        self.assertIsInstance(url, URL)
        self.assertEqual(url.scheme, "tcp")
        self.assertEqual(url.site.host, "::")
        self.assertEqual(s.name(), (url.site.host, url.site.port))
        self.assertEqual(s.family(), ip.PF_INET6)
        self.tryConnectToServer(s)
        del s
        self.assertIsNone(ref())

    def test_tcpserver_hostname(self):
        hostname = _socket.gethostname()
        hostaddress, hostport = ip.resolve(hostname, 0)
        s = TcpServer(addr=hostname, options=self.options)
        s.newConnection.connect(self.__newconnection)
        ref = weakref.ref(s)
        url = s.url()        
        self.assertIsInstance(url, URL)
        self.assertEqual(url.scheme, "tcp")
        self.assertEqual(url.site.host, hostaddress)
        self.assertEqual(s.name(), (url.site.host, url.site.port))
        self.tryConnectToServer(s)
        del s
        self.assertIsNone(ref())

# -------------------------------------------------------------------

def suite():
    tests = list((t,tuple()) for t in TestTcpServer.__dict__ \
                             if t.startswith("test_"))
    tests += list((t,("nodelay",)) for t in TestTcpServer.__dict__ \
                                   if t.startswith("test_"))
    return unittest.TestSuite(map(TestTcpServer, tests))    

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
