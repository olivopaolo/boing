# -*- coding: utf-8 -*-
#
# boing/net/tcp.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import logging
import socket as _socket

from PyQt4.QtNetwork import QAbstractSocket, QHostAddress, QTcpSocket, QTcpServer

import boing.net.ip as ip
from boing.utils.url import URL

class TcpSocket(QTcpSocket):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger("TcpSocket.%d"%id(self))
        self.error.connect(self.__error)
        
    def __error(self, error):
        if error!=QAbstractSocket.RemoteHostClosedError:
            raise RuntimeError(self.errorString())

    def connect(self, host, port, family=None):
        """Raises Exception if host cannot be resolved."""        
        host, port = ip.resolve(host, port,
                                family if family is not None else 0,
                                _socket.SOCK_STREAM)[:2]
        self.connectToHost(host, port)
        return self

    def family(self):
        addr = self.localAddress()        
        if addr.protocol()==QAbstractSocket.IPv4Protocol:
            family = ip.PF_INET
        elif addr.protocol()==QAbstractSocket.IPv6Protocol:
            family = ip.PF_INET6
        else: family = None
        return family
        
    def name(self):
        """Return the server socket’s address (host, port)."""
        return ip.addrToString(self.localAddress()), self.localPort()

    def peerName(self):
        return ip.addrToString(self.peerAddress()), self.peerPort()

    def peerUrl(self):
        url = URL()
        url.scheme = "tcp"
        url.site.host, url.site.port = self.peerName()
        return url

    def read(self):
        return self.receive()

    def receive(self):
        size = self.bytesAvailable()
        if size>0: return self.readData(size)
        else: return bytes()

    def receiveFrom(self):
        size = self.bytesAvailable()
        if size>0: return self.readData(size), self.peerName()
        else: return bytes(), None

    def setOption(self, option):
        if option=="nodelay":
            self.setSocketOption(QAbstractSocket.LowDelayOption, 1)

    def send(self, data):
        if self.state()==QAbstractSocket.ConnectedState:
            return self.write(data)
        else: 
            self.logger.warning("send method invoked on disconnected socket.")
            return 0

    def url(self):
        """Return the socket's URL, i.e. tcp://<host>:<port>."""
        url = URL()
        url.scheme = "tcp"
        url.site.host, url.site.port = self.name()
        return url
    
# -------------------------------------------------------------------------

def TcpConnection(url, family=None):
    """Raises Exception if host cannot be resolved."""
    if not isinstance(url, URL): url = URL(url)
    if not url.site.host: 
        raise ValueError("Target host is mandatory: %s"%url)
    elif url.site.port==0: 
        raise ValueError("Target port is mandatory: %s"%url)
    else:
        socket = TcpSocket()
        socket.connect(url.site.host, url.site.port, family)
    return socket

# -------------------------------------------------------------------

class TcpServer(QTcpServer):

    def __init__(self, host=None, port=0, family=None,
                 maxconnections=30, factory=TcpSocket, options=tuple(),
                 *args, **kwargs):
        """Raises Exception if TCP socket cannot be bound at specified
        host and port."""
        super().__init__(*args, **kwargs)
        self.__factory = factory
        self.__options = options if options is not None else tuple()
        self.setMaxPendingConnections(maxconnections)
        if not host: 
            if family==ip.PF_INET6: host = QHostAddress.AnyIPv6
            else: host = QHostAddress.Any
        if not QHostAddress(host) in (QHostAddress.Any, 
                                      QHostAddress.AnyIPv6):
            host, port = ip.resolve(host, port, 
                                    family if family is not None else 0, 
                                    _socket.SOCK_STREAM)[:2]
        if not self.listen(QHostAddress(host), int(port)):
            raise Exception(self.errorString())

    def incomingConnection(self, descriptor):
        connection = self.__factory(self)
        for option in self.__options: connection.setOption(option)
        connection.setSocketDescriptor(descriptor)
        self.addPendingConnection(connection)        

    def family(self):
        addr = self.serverAddress()        
        if addr.protocol()==QAbstractSocket.IPv4Protocol:
            family = ip.PF_INET
        elif addr.protocol()==QAbstractSocket.IPv6Protocol:
            family = ip.PF_INET6
        else: family = None
        return family

    def name(self):
        """Return the server socket’s address (host, port)."""
        return ip.addrToString(self.serverAddress()), self.serverPort()

    def url(self):
        """Return the socket's URL, i.e. tcp://<host>:<port>."""
        url = URL()
        url.scheme = "tcp"
        url.site.host, url.site.port = self.name()
        return url

# -------------------------------------------------------------------

class EchoSocket(TcpSocket):
    
    def __init__(self, parent=None):
        TcpSocket.__init__(self, parent)
        self.logger = logging.getLogger("EchoSocket.%d"%id(self))
        self.readyRead.connect(self.__echoData)
        self.disconnected.connect(self.__disconnected)

    def setSocketDescriptor(self, descriptor):
        TcpSocket.setSocketDescriptor(self, descriptor)
        if self.state()==QAbstractSocket.ConnectedState:
            self.logger.debug("New client: %s"%str(self.peerName()))

    def __disconnected(self):
        self.logger.debug("Lost client: %s"%str(self.peerName()))
        
    def __echoData(self):
        data, peer = self.receiveFrom()
        self.logger.debug("%s: %s"%(peer, data))
        self.send(data)
    
def EchoServer(host=None, port=0, family=None, maxconnections=30):
    return TcpServer(host, port, family, maxconnections, EchoSocket)
