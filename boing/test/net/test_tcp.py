#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# boing/test/net/test_tcp.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import itertools
import socket as _socket
import sys
import unittest
import weakref

from PyQt4 import QtCore
from PyQt4.QtNetwork import QAbstractSocket, QHostAddress

import boing.net.ip as ip
import boing.net.tcp as tcp
from boing.utils.url import URL

class TestTcpSocket(QtCore.QObject, unittest.TestCase):

    def __init__(self, *argv, **kwargs):
        QtCore.QObject.__init__(self)
        unittest.TestCase.__init__(self, *argv, **kwargs)

    def setUp(self):
        self.data = b"boing-unittest"
        self.result = None
        self.app = QtCore.QCoreApplication(sys.argv)

    def tearDown(self):
        self.app.exit()
        self.app = None
    
    def __send_data(self, sock):
        sock.send(self.data)

    def __readdata(self):
        conn = self.sender() 
        self.result = conn.receive()
        self.app.quit()

    def test_tcpconnection_loopback_ip4(self):
        serv = tcp.EchoServer(host="0.0.0.0")
        conn = tcp.TcpConnection("tcp://127.0.0.1:%d"%serv.name()[1])
        conn.readyRead.connect(self.__readdata)
        QtCore.QTimer.singleShot(100, lambda:self.__send_data(conn))
        QtCore.QTimer.singleShot(1000, self.app.quit)
        self.app.exec_()
        url = conn.url()
        peerurl = conn.peerUrl()
        self.assertIsInstance(url, URL)
        self.assertEqual(url.scheme, "tcp")
        self.assertEqual(conn.name(), (url.site.host, url.site.port))
        self.assertEqual(conn.peerName(), (peerurl.site.host, peerurl.site.port))
        self.assertEqual(peerurl.site.host, "127.0.0.1")
        self.assertEqual(peerurl.site.port, serv.name()[1])
        self.assertEqual(self.data, self.result)
        conn.close()

    def test_tcpconnection_loopback_ip6(self):
        serv = tcp.EchoServer(host="::")
        conn = tcp.TcpConnection("tcp://[::1]:%d"%serv.name()[1])
        conn.readyRead.connect(self.__readdata)
        QtCore.QTimer.singleShot(100, lambda:self.__send_data(conn))
        QtCore.QTimer.singleShot(1000, self.app.quit)
        self.app.exec_()
        url = conn.url()
        peerurl = conn.peerUrl()
        self.assertIsInstance(url, URL)
        self.assertEqual(url.scheme, "tcp")
        self.assertEqual(conn.name(), (url.site.host, url.site.port))
        self.assertEqual(conn.peerName(), (peerurl.site.host, peerurl.site.port))
        self.assertEqual(peerurl.site.host, "::1")
        self.assertEqual(peerurl.site.port, serv.name()[1])
        self.assertEqual(self.data, self.result)
        conn.close()

    def test_tcpconnection_localhost_ip4(self):
        serv = tcp.EchoServer(host="0.0.0.0")
        conn = tcp.TcpConnection("tcp://localhost:%d"%serv.name()[1], ip.PF_INET)
        conn.readyRead.connect(self.__readdata)
        QtCore.QTimer.singleShot(100, lambda:self.__send_data(conn))
        QtCore.QTimer.singleShot(1000, self.app.quit)
        self.app.exec_()
        url = conn.url()
        peerurl = conn.peerUrl()
        self.assertIsInstance(url, URL)
        self.assertEqual(url.scheme, "tcp")
        self.assertEqual(conn.name(), (url.site.host, url.site.port))
        self.assertEqual(conn.peerName(), (peerurl.site.host, peerurl.site.port))
        self.assertEqual(peerurl.site.host, "127.0.0.1")
        self.assertEqual(peerurl.site.port, serv.name()[1])
        self.assertEqual(self.data, self.result)
        conn.close()

    def test_tcpconnection_localhost_ip6(self):
        try:
            hostaddress, hostport = ip.resolve("localhost", 0, ip.PF_INET6)
        except Exception:
            hostaddress, hostport = None, 0
        if hostaddress is not None:
            serv = tcp.EchoServer(host="::")
            conn = tcp.TcpConnection("tcp://localhost:%d"%serv.name()[1], ip.PF_INET6)
            conn.readyRead.connect(self.__readdata)
            QtCore.QTimer.singleShot(100, lambda:self.__send_data(conn))
            QtCore.QTimer.singleShot(1000, self.app.quit)
            self.app.exec_()
            url = conn.url()
            peerurl = conn.peerUrl()
            self.assertIsInstance(url, URL)
            self.assertEqual(url.scheme, "tcp")
            self.assertEqual(conn.name(), (url.site.host, url.site.port))
            self.assertEqual(conn.peerName(), (peerurl.site.host, peerurl.site.port))
            self.assertEqual(peerurl.site.host, "::1")
            self.assertEqual(peerurl.site.port, serv.name()[1])
            self.assertEqual(self.data, self.result)
            conn.close()

    def test_tcpconnection_hostname_ip4(self):
        hostname = _socket.gethostname()
        try:
            hostaddress, hostport = ip.resolve(hostname, 0, ip.PF_INET)
        except Exception:
            hostaddress, hostport = None, 0
        if hostaddress is not None:
            serv = tcp.EchoServer(host="0.0.0.0")
            conn = tcp.TcpConnection("tcp://%s:%d"%(hostname, serv.name()[1]), 
                                 ip.PF_INET)
            conn.readyRead.connect(self.__readdata)
            QtCore.QTimer.singleShot(100, lambda:self.__send_data(conn))
            QtCore.QTimer.singleShot(1000, self.app.quit)
            self.app.exec_()
            url = conn.url()
            peerurl = conn.peerUrl()
            self.assertIsInstance(url, URL)
            self.assertEqual(url.scheme, "tcp")
            self.assertEqual(conn.name(), (url.site.host, url.site.port))
            self.assertEqual(conn.peerName(), (peerurl.site.host, 
                                               peerurl.site.port))
            self.assertEqual(peerurl.site.host, hostaddress)
            self.assertEqual(peerurl.site.port, serv.name()[1])
            self.assertEqual(self.data, self.result)
            conn.close()

    def test_tcpconnection_hostname_ip6(self):
        hostname = _socket.gethostname()
        try:
            hostaddress, hostport = ip.resolve(hostname, 0, ip.PF_INET6)
        except Exception:
            hostaddress, hostport = None, 0
        if hostaddress is not None:
            serv = tcp.EchoServer(host="::")
            conn = tcp.TcpConnection("tcp://%s:%d"%(hostname, serv.name()[1]), 
                                 ip.PF_INET6)
            conn.readyRead.connect(self.__readdata)
            QtCore.QTimer.singleShot(100, lambda:self.__send_data(conn))
            QtCore.QTimer.singleShot(1000, self.app.quit)
            self.app.exec_()
            url = conn.url()
            peerurl = conn.peerUrl()
            self.assertIsInstance(url, URL)
            self.assertEqual(url.scheme, "tcp")
            self.assertEqual(conn.name(), (url.site.host, url.site.port))
            self.assertEqual(conn.peerName(), (peerurl.site.host, 
                                               peerurl.site.port))
            self.assertEqual(peerurl.site.host, "::1")
            self.assertEqual(peerurl.site.port, serv.name()[1])
            self.assertEqual(self.data, self.result)
            conn.close()

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
        elif QHostAddress(addr)==QHostAddress.AnyIPv6 \
                or addr=="::ffff::":
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
        self.assertIsInstance(conn, tcp.TcpSocket)
        self.assertEqual(conn.state(), QAbstractSocket.ConnectedState)
        self.assertEqual(sockname, conn.peerName())
        conn.close()
        self.assertEqual(self.result, self.data)
        self.connections = None

    def test_tcpserver_empty(self):
        s = tcp.TcpServer()
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
        s = tcp.TcpServer(host="localhost")
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
        s = tcp.TcpServer(host="127.0.0.1")
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
        s = tcp.TcpServer(host="::1")
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
        s = tcp.TcpServer(host="0.0.0.0")
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
        s = tcp.TcpServer(host="::")
        s.newConnection.connect(self.__newconnection)
        ref = weakref.ref(s)
        url = s.url()        
        self.assertIsInstance(url, URL)
        self.assertEqual(url.scheme, "tcp")
        #self.assertEqual(url.site.host, "::")
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
            s = tcp.TcpServer(host=hostname, family=ip.PF_INET)
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
            s = tcp.TcpServer(host=hostname, family=ip.PF_INET6)
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
        s = tcp.TcpServer(options=("nodelay",))
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
        s = tcp.TcpServer(host="localhost", options=("nodelay",))
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
        s = tcp.TcpServer(host="127.0.0.1", options=("nodelay",))
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
        s = tcp.TcpServer(host="::1", options=("nodelay",))
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
        s = tcp.TcpServer(host="0.0.0.0", options=("nodelay",))
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
        s = tcp.TcpServer(host="::", options=("nodelay",))
        s.newConnection.connect(self.__newconnection)
        ref = weakref.ref(s)
        url = s.url()        
        self.assertIsInstance(url, URL)
        self.assertEqual(url.scheme, "tcp")
        #self.assertEqual(url.site.host, "::")
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
            s = tcp.TcpServer(host=hostname, family=ip.PF_INET, options=("nodelay",))
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
            s = tcp.TcpServer(host=hostname, family=ip.PF_INET6, options=("nodelay",))
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
    testcases = (
        TestTcpSocket,
        TestTcpServer,
        )
    return unittest.TestSuite(itertools.chain(
            *(map(t, filter(lambda f: f.startswith("test_"), dir(t))) \
                  for t in testcases)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
