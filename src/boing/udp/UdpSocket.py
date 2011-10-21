# -*- coding: utf-8 -*-
#
# boing/udp/UdpSocket.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import socket as _socket

from PyQt4.QtNetwork import QAbstractSocket, QHostAddress, QUdpSocket

from boing import ip
from boing.url import URL

class UdpSocket(QUdpSocket):

    # http://en.wikipedia.org/wiki/IPv4
    # http://en.wikipedia.org/wiki/Ipv6
    # http://gsyc.escet.urjc.es/~eva/IPv6-web/ipv6.html

    # TODO: Multicast will be supported in Qt4.8
    # http://doc.qt.nokia.com/4.8/qudpsocket.html

    def __init__(self, parent=None):
        super().__init__(parent)

    # ---------------------------------------------------------------------
                
    def bind(self, addr=QHostAddress.Any, port=0, 
             mode=QUdpSocket.DontShareAddress):
        if not addr: addr = QHostAddress.Any
        if not QHostAddress(addr) in (QHostAddress.Any, 
                                      QHostAddress.AnyIPv6):
            addr, port = ip.resolve(addr, port, type=_socket.SOCK_DGRAM)[:2]
        if not super().bind(QHostAddress(addr), port, mode):
            raise Exception(self.errorString())
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

    def receive(self):
        size = self.pendingDatagramSize()
        if size>0: return self.readDatagram(size)[0]
        else: return None

    def receiveFrom(self):
        size = self.pendingDatagramSize()
        if size>0:
            data, addr, port = self.readDatagram(size)
            return data, (ip.addrToString(addr), port)
        else: return None, None

    def url(self):
        """Return the socket's URL, i.e. tcp://<host>:<port>."""
        url = URL()
        url.scheme = "tcp"
        url.site.host, url.site.port = self.name()
        return url

    # ---------------------------------------------------------------------
    # Disconnected mode
    
    def sendTo(self, data, addr, port, resolve=True):
        if resolve: addr, port = ip.resolve(addr, port, type=_socket.SOCK_DGRAM)[:2]
        return self.writeDatagram(data, QHostAddress(addr), port)

    # ---------------------------------------------------------------------
    # Connected mode

    def connect(self, addr, port):
        addr, port = ip.resolve(addr, port, type=_socket.SOCK_DGRAM)[:2]
        self.connectToHost(addr, port)
        return self

    def peerName(self):
        return ip.addrToString(self.peerAddress()), self.peerPort()

    def peerUrl(self):
        url = URL()
        url.scheme = "tcp"
        url.site.host, url.site.port = self.peerName()
        return url

    def send(self, data):
        return self.write(data)

    """
    # ---------------------------------------------------------------------
    # Multicast mode
    
    def isMulticast(self):
        if sys.platform=='win32':
            h = _socket.inet_aton(self.__sock.getsockname()[0])
        else:
            h = _socket.inet_pton(self.__sock.family, self.__sock.getsockname()[0])
        return (self.__sock.family==ip.PF_INET and ip.IN_MULTICAST(h)) or (self.__sock.family==ip.PF_INET6 and ip.IN6_IS_ADDR_MULTICAST(h))

    def setMulticastTTL(self, ttl):
        #1=subnet, 31=site, 64=national, >=127=worldwide#
        if self.__sock.family==ip.PF_INET6:
            level, optname = _socket.IPPROTO_IPV6, _socket.IPV6_MULTICAST_HOPS
        else:
            level, optname = _socket.IPPROTO_IP, _socket.IP_MULTICAST_TTL
        self.__sock.setsockopt(level, optname, ttl)
            
    def setMulticastLoopback(self, boolean):
        if self.__sock.family==ip.PF_INET6:
            level, optname = _socket.IPPROTO_IPV6, _socket.IPV6_MULTICAST_LOOP
        else:
            level, optname = _socket.IPPROTO_IP, _socket.IP_MULTICAST_TTL
        self.__sock.setsockopt(level, optname, 1 if boolean else 0)"""

# -------------------------------------------------------------------------

def UdpListener(url="udp://0.0.0.0:0", options=tuple()):
    if not isinstance(url, URL): url = URL(url)
    s = UdpSocket()
    if "reuse" in options:
        kwargs = {"mode": QUdpSocket.ShareAddress|QUdpSocket.ReuseAddressHint}
    else: 
        kwargs = {}
    return s.bind(url.site.host, url.site.port, **kwargs)

def UdpSender(url):
    if not isinstance(url, URL): url = URL(url)
    s = UdpSocket()
    return s.connect(url.site.host, url.site.port)

# -------------------------------------------------------------------------

if __name__=="__main__":
    listener = UdpListener("udp://:0")
    url = listener.url()
    sender = UdpSender(listener.url())
    sender.send(b"hello!")
    print(listener.receive())
    # FIXME: below...
    #u = UdpListener()
    #u.sendTo(b"hello echo", ("",7)) # echo ?
    #print(u.receive())
