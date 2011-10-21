# -*- coding: utf-8 -*-
#
# boing/tcp/TcpServer.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import socket as _socket

from PyQt4.QtNetwork import QAbstractSocket, QHostAddress, QTcpServer

from boing import ip
from boing.tcp.TcpSocket import TcpSocket
from boing.url import URL

class TcpServer(QTcpServer):

    def __init__(self, addr=QHostAddress.Any, port=0, 
                 maxconnections=30, factory=TcpSocket, options=tuple()):
        super().__init__(parent=None)
        self.__factory = factory
        self.__options = options if options is not None else tuple()
        self.setMaxPendingConnections(maxconnections)
        if not addr: addr = QHostAddress.Any
        if not QHostAddress(addr) in (QHostAddress.Any, 
                                      QHostAddress.AnyIPv6):
            addr, port = ip.resolve(addr, port, type=_socket.SOCK_STREAM)[:2]
        if not self.listen(QHostAddress(addr), int(port)):
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

if __name__=="__main__":
    import datetime
    import traceback
    from boing.eventloop.EventLoop import EventLoop
    def newClient():
        connection = server.nextPendingConnection()
        client = connection.name()
        peer = connection.peerName()
        try:
            identd = TcpSocket().connect((peer[0],113))
            identd.send("%d, %d\n"%(peer[1], client[1]))
            identity = identd.receive()
            identd.close()
        except:
            #traceback.print_exc()
            identity = "[Unknown]"
        connection.send(b"HTTP/1.0 200 OK\n\n")
        connection.send(b"<html><body><pre>")
        connection.send(("Timestamp: %s\n"%datetime.datetime.now().isoformat()).encode())
        connection.send(("Identity: %s\n"%identity).encode())
        connection.send(b"</pre></body></html>")
        connection.close()
    server = TcpServer() 
    server.newConnection.connect(newClient)
    #options=("nodelay","fastack","reuse","nosigpipe"), 
    print("EchoServer listening at", server.url())
    EventLoop.run()
    del server
