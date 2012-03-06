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
import sys

from PyQt4 import QtCore
from PyQt4.QtNetwork import QAbstractSocket, QHostAddress

from boing import ip
from boing.tcp.TcpSocket import TcpSocket
from boing.tcp.TcpServer import TcpServer
from boing.url import URL

class TestTcpServer(QtCore.QObject, unittest.TestCase):
    
    def __init__(self, methodname):
        QtCore.QObject.__init__(self)
        unittest.TestCase.__init__(self, methodname)

    def setUp(self):
        self.connections = []
        self.data = b"boing-unittest"
        self.result = None
        self.app = QtCore.QCoreApplication(sys.argv)

    def tearDown(self):
        self.app.exit()
        self.app = None

    def __readdata(self):
        conn = self.sender() 
        self.result = conn.receive()
        self.app.quit()

    def __newconnection(self):
        server = self.sender()
        conn = server.nextPendingConnection()
        conn.readyRead.connect(self.__readdata)
        self.connections.append(conn)

    def tryConnectToServer(self, server):
        s = _socket.socket(server.family(), _socket.SOCK_STREAM)
        addr, port = server.name()
        if QHostAddress(addr)==QHostAddress.Any:
            addr = "127.0.0.1"
        elif QHostAddress(addr)==QHostAddress.AnyIPv6:
            addr = "::1"
        s.connect((addr, port))
        s.send(self.data)
        QtCore.QTimer.singleShot(1000, self.app.quit)
        self.app.exec_()
        sockname = s.getsockname()[:2]
        if(server.family()==ip.PF_INET6):
            sockname = (sockname[0].partition("%")[0], sockname[1])
        s.close()
        self.assertEqual(len(self.connections), 1)        
        conn = self.connections[0]
        self.assertIsInstance(conn, TcpSocket)
        self.assertEqual(conn.state(), QAbstractSocket.ConnectedState)
        self.assertEqual(sockname, conn.peerName())
        conn.close()
        self.assertEqual(self.result, self.data)
        self.connections = None

    def test_tcpserver_empty(self):
        s = TcpServer()
        s.newConnection.connect(self.__newconnection)
        ref = weakref.ref(s)
        url = s.url()
        self.assertIsInstance(url, URL)
        self.assertEqual(url.scheme, "tcp")
        self.assertEqual(s.name(), (url.site.host, url.site.port))
        self.assertIn(s.family(), (ip.PF_INET, ip.PF_INET6))
        self.tryConnectToServer(s)
        del s
        self.assertIsNone(ref())

    def test_tcpserver_localhost(self):
        s = TcpServer(host="localhost")
        s.newConnection.connect(self.__newconnection)
        ref = weakref.ref(s)
        url = s.url()
        self.assertIsInstance(url, URL)
        self.assertEqual(url.scheme, "tcp")
        self.assertIn(url.site.host, ("127.0.0.1", "::1"))
        self.assertIsInstance(url.site.port, int)
        self.assertEqual(s.name(), (url.site.host, url.site.port))
        self.assertIn(s.family(), (ip.PF_INET, ip.PF_INET6))
        self.tryConnectToServer(s)
        del s
        self.assertIsNone(ref())

    def test_tcpserver_localhost_IPv4(self):
        s = TcpServer(host="127.0.0.1")
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
        s = TcpServer(host="::1")
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

    def test_tcpserver_any_IPv4(self):
        s = TcpServer(host="0.0.0.0")
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
        s = TcpServer(host="::")
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

    def test_tcpserver_hostname_IPv4(self):
        hostname = _socket.gethostname()
        try:
            hostaddress, hostport = ip.resolve(hostname, 0, ip.PF_INET)
        except Exception:
            hostaddress, hostport = None, 0
        if hostaddress is not None:
            s = TcpServer(host=hostname, family=ip.PF_INET)
            s.newConnection.connect(self.__newconnection)
            ref = weakref.ref(s)
            url = s.url()        
            self.assertIsInstance(url, URL)
            self.assertEqual(url.scheme, "tcp")
            self.assertEqual(hostaddress, url.site.host)
            self.assertEqual(s.name(), (url.site.host, url.site.port))
            self.tryConnectToServer(s)
            del s
            self.assertIsNone(ref())

    def test_tcpserver_hostname_IPv6(self):
        hostname = _socket.gethostname()
        try:
            hostaddress, hostport = ip.resolve(hostname, 0, ip.PF_INET6)[:2]
        except Exception:
            hostaddress, hostport = None, 0
        if hostaddress is not None:
            s = TcpServer(host=hostname, family=ip.PF_INET6)
            s.newConnection.connect(self.__newconnection)
            ref = weakref.ref(s)
            url = s.url()        
            self.assertIsInstance(url, URL)
            self.assertEqual(url.scheme, "tcp")
            self.assertEqual(hostaddress.partition("%")[0], url.site.host)
            self.assertEqual(s.name(), (url.site.host, url.site.port))
            self.tryConnectToServer(s)
            del s
            self.assertIsNone(ref())

    # ---------------------------------------------------------------------
    # "nodelay" option cases    

    def test_tcpserver_empty_nodelay(self):
        s = TcpServer(options=("nodelay",))
        s.newConnection.connect(self.__newconnection)
        ref = weakref.ref(s)
        url = s.url()
        self.assertIsInstance(url, URL)
        self.assertEqual(url.scheme, "tcp")
        self.assertEqual(s.name(), (url.site.host, url.site.port))
        self.assertIn(s.family(), (ip.PF_INET, ip.PF_INET6))
        self.tryConnectToServer(s)
        del s
        self.assertIsNone(ref())

    def test_tcpserver_localhost_nodelay(self):
        s = TcpServer(host="localhost", options=("nodelay",))
        s.newConnection.connect(self.__newconnection)
        ref = weakref.ref(s)
        url = s.url()
        self.assertIsInstance(url, URL)
        self.assertEqual(url.scheme, "tcp")
        self.assertIn(url.site.host, ("127.0.0.1", "::1"))
        self.assertIsInstance(url.site.port, int)
        self.assertEqual(s.name(), (url.site.host, url.site.port))
        self.assertIn(s.family(), (ip.PF_INET, ip.PF_INET6))
        self.tryConnectToServer(s)
        del s
        self.assertIsNone(ref())

    def test_tcpserver_localhost_IPv4_nodelay(self):
        s = TcpServer(host="127.0.0.1", options=("nodelay",))
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

    def test_tcpserver_localhost_IPv6_nodelay(self):
        s = TcpServer(host="::1", options=("nodelay",))
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

    def test_tcpserver_any_IPv4_nodelay(self):
        s = TcpServer(host="0.0.0.0", options=("nodelay",))
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

    def test_tcpserver_any_IPv6_nodelay(self):
        s = TcpServer(host="::", options=("nodelay",))
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

    def test_tcpserver_hostname_IPv4_nodelay(self):
        hostname = _socket.gethostname()
        try:
            hostaddress, hostport = ip.resolve(hostname, 0, ip.PF_INET)
        except Exception:
            hostaddress, hostport = None, 0
        if hostaddress is not None:
            s = TcpServer(host=hostname, family=ip.PF_INET, options=("nodelay",))
            s.newConnection.connect(self.__newconnection)
            ref = weakref.ref(s)
            url = s.url()        
            self.assertIsInstance(url, URL)
            self.assertEqual(url.scheme, "tcp")
            self.assertEqual(hostaddress, url.site.host)
            self.assertEqual(s.name(), (url.site.host, url.site.port))
            self.tryConnectToServer(s)
            del s
            self.assertIsNone(ref())

    def test_tcpserver_hostname_IPv6_nodelay(self):
        hostname = _socket.gethostname()
        try:
            hostaddress, hostport = ip.resolve(hostname, 0, ip.PF_INET6)
        except Exception:
            hostaddress, hostport = None, 0
        if hostaddress is not None:
            s = TcpServer(host=hostname, family=ip.PF_INET6, options=("nodelay",))
            s.newConnection.connect(self.__newconnection)
            ref = weakref.ref(s)
            url = s.url()        
            self.assertIsInstance(url, URL)
            self.assertEqual(url.scheme, "tcp")
            self.assertEqual(hostaddress.partition("%")[0], url.site.host)
            self.assertEqual(s.name(), (url.site.host, url.site.port))
            self.tryConnectToServer(s)
            del s
            self.assertIsNone(ref())

# -------------------------------------------------------------------

def suite():
    tests = (t for t in TestTcpServer.__dict__ if t.startswith("test_"))
    return unittest.TestSuite(map(TestTcpServer, tests))    

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
