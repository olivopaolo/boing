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
        QUdpSocket.__init__(self, parent)
        self.__open = False
        self.error.connect(self.__error)
        self.connected.connect(self.__connected)
        
    def __error(self, error):
        if error not in (QAbstractSocket.RemoteHostClosedError,
                         QAbstractSocket.AddressInUseError) :
            raise RuntimeError(self.errorString())

    def isOpen(self):
        return self.__open
    # ---------------------------------------------------------------------
                
    def bind(self, host=None, port=0, family=None,
             mode=QUdpSocket.DontShareAddress):
        """Raises Exception if UDP socket cannot be bound at specified
        host and port."""
        if not host: 
            if family==ip.PF_INET: host = QHostAddress.Any
            else: host = QHostAddress.AnyIPv6
        if not QHostAddress(host) in (QHostAddress.Any, 
                                      QHostAddress.AnyIPv6):
            host, port = ip.resolve(host, port, 
                                    family if family is not None else 0, 
                                    _socket.SOCK_DGRAM)[:2]
        if not QUdpSocket.bind(self, QHostAddress(host), port, mode):
            raise Exception(self.errorString())
        self.__open = True
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

    def read(self):
        return self.receive()

    def receive(self):
        size = self.pendingDatagramSize()
        if size>0: return self.readDatagram(size)[0]
        else: return bytes()

    def receiveFrom(self):
        size = self.pendingDatagramSize()
        if size>0:
            data, addr, port = self.readDatagram(size)
            return data, (ip.addrToString(addr), port)
        else: return bytes(), None

    def url(self):
        """Return the socket's URL, i.e. tcp://<host>:<port>."""
        url = URL()
        url.scheme = "udp"
        url.site.host, url.site.port = self.name()
        return url

    # ---------------------------------------------------------------------
    # Disconnected mode
    
    def sendTo(self, data, host, port, family=None, resolve=True):
        """Raises Exception if host cannot be resolved."""
        if resolve: 
            host, port = ip.resolve(host, port, 
                                    family if family is not None else 0,
                                    _socket.SOCK_DGRAM)[:2]
        return self.writeDatagram(data, QHostAddress(host), port)

    # ---------------------------------------------------------------------
    # Connected mode

    def connect(self, host, port, family=None):
        """Raises Exception if host cannot be resolved or connected."""
        host, port = ip.resolve(host, port,
                                family if family is not None else 0,
                                _socket.SOCK_DGRAM)[:2]
        self.connectToHost(host, port)
        return self

    def __connected(self):
        self.__open = True

    def peerName(self):
        return ip.addrToString(self.peerAddress()), self.peerPort()

    def peerUrl(self):
        url = URL()
        url.scheme = "udp"
        url.site.host, url.site.port = self.peerName()
        return url

    def send(self, data):
        if self.state()==QAbstractSocket.ConnectedState:
            return self.write(data)
        else: 
            self.logger.warning("send method invoked on disconnected socket.")
            return 0

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

def UdpListener(url=None, family=None, options=tuple()):
    """Raises Exception if UDP socket cannot be bound at specified
    host and port."""    
    if not isinstance(url, URL): url = URL(url)
    s = UdpSocket()
    if "reuse" in options:
        kwargs = {"mode": QUdpSocket.ReuseAddressHint}
    else: 
        kwargs = {}
    return s.bind(url.site.host, url.site.port, family, **kwargs)

def UdpSender(url, family=None):
    """Raises Exception if host cannot be resolved or connected."""
    if not isinstance(url, URL): url = URL(url)
    s = UdpSocket()
    return s.connect(url.site.host, url.site.port, family)

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
