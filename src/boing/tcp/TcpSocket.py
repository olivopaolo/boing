# -*- coding: utf-8 -*-
#
# boing/tcp/TcpSocket.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import logging
import socket as _socket

from PyQt4.QtNetwork import QAbstractSocket, QHostAddress, QTcpSocket

from boing import ip
from boing.url import URL

class TcpSocket(QTcpSocket):

    def __init__(self, parent=None):
        QTcpSocket.__init__(self, parent)
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
    socket = TcpSocket()
    socket.connect(url.site.host, url.site.port, family)
    return socket

# -------------------------------------------------------------------------

if __name__=="__main__":
    import sys
    import traceback
    from boing.eventloop.EventLoop import EventLoop
    try: url = URL(sys.argv[1])
    except: 
        traceback.print_exc()
        url = URL("http://127.0.0.1:80")
    def dumpdata():
        print(c.receive())
    def send_data(tid):
        data = "HEAD %s HTTP/1.0\n\n"%url.path
        c.send(data.encode())
    c = TcpConnection(url)
    c.readyRead.connect(dumpdata)
    c.disconnected.connect(EventLoop.stop)
    EventLoop.after(.1, send_data)
    EventLoop.run()
    c.close()

