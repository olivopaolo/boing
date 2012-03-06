# -*- coding: utf-8 -*-
#
# boing/tcp/TcpServer.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import logging
import socket as _socket

from PyQt4.QtNetwork import QAbstractSocket, QHostAddress, QTcpServer

from boing import ip
from boing.tcp.TcpSocket import TcpSocket
from boing.url import URL

class TcpServer(QTcpServer):

    def __init__(self, host=None, port=0, family=None,
                 maxconnections=30, factory=TcpSocket, options=tuple(), parent=None):
        """Raises Exception if TCP socket cannot be bound at specified
        host and port."""
        QTcpServer.__init__(self, parent=parent)
        self.__factory = factory
        self.__options = options if options is not None else tuple()
        self.setMaxPendingConnections(maxconnections)
        if not host: 
            if family==ip.PF_INET: host = QHostAddress.Any
            else: host = QHostAddress.AnyIPv6
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

# -------------------------------------------------------------------

if __name__=="__main__":
    import logging
    import sys
    from PyQt4 import QtCore
    app = QtCore.QCoreApplication(sys.argv)
    logging.basicConfig(level=logging.getLevelName("DEBUG"))
    server = EchoServer()
    print("EchoServer listening at", server.url())
    sys.exit(app.exec_())

