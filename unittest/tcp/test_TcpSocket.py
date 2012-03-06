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
import sys

from PyQt4 import QtCore

from boing import ip
from boing.tcp.TcpServer import EchoServer
from boing.tcp.TcpSocket import TcpSocket, TcpConnection
from boing.url import URL

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
        serv = EchoServer(host="0.0.0.0")
        conn = TcpConnection("tcp://127.0.0.1:%d"%serv.name()[1])
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
        serv = EchoServer(host="::")
        conn = TcpConnection("tcp://[::1]:%d"%serv.name()[1])
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
        serv = EchoServer(host="0.0.0.0")
        conn = TcpConnection("tcp://localhost:%d"%serv.name()[1], ip.PF_INET)
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
            serv = EchoServer(host="::")
            conn = TcpConnection("tcp://localhost:%d"%serv.name()[1], ip.PF_INET6)
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
            serv = EchoServer(host="0.0.0.0")
            conn = TcpConnection("tcp://%s:%d"%(hostname, serv.name()[1]), 
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
            serv = EchoServer(host="::")
            conn = TcpConnection("tcp://%s:%d"%(hostname, serv.name()[1]), 
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

# -------------------------------------------------------------------

def suite():
    tests = (t for t in TestTcpSocket.__dict__ if t.startswith("test_"))
    return unittest.TestSuite(map(TestTcpSocket, tests))    

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
