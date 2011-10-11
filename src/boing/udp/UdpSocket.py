# -*- coding: utf-8 -*-
#
# boing/udp/UdpSocket.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import socket
import struct
import sys

from boing import ip
from boing.url import URL

class UdpSocket(object):

    # http://en.wikipedia.org/wiki/IPv4
    # http://en.wikipedia.org/wiki/Ipv6
    # http://gsyc.escet.urjc.es/~eva/IPv6-web/ipv6.html

    # FIXME: add support for broadcast UDP?

    # "sysctl net.inet.udp.maxdgram" returns 9216 on OS X
    # "sysctl net.inet.udp.recvspace" returns 42080 on OS X

    def __init__(self, family=ip.PF_INET):
        if family not in (ip.PF_INET, ip.PF_INET6):
            raise ValueError("Unsupported protocol family (use PF_INET or PF_INET6)")
        self.__sock = socket.socket(family, socket.SOCK_DGRAM, 0)
        self.__recvspace = self.getReceiveBufferSize()
        #self.setBufferSizes(-1,-1)

    def fileno(self):
        return self.__sock.fileno()

    def getSocket(self):
        return self.__sock

    def __del__(self):
        #self.__sock.shutdown(SHUT_RDWR) FIXME?
        self.__sock.close()

    # ---------------------------------------------------------------------
    # Send/receive buffer size
    
    def __setMaxBufferSize(self, optname):
        for i in range(30, 0, -1):
            try:
                s = 1 << i
                self.__sock.setsockopt(socket.SOL_SOCKET, optname, s)
                return s
            except:
                #traceback.print_exc()
                pass
        
    def setBufferSizes(self, ssize, rsize):
        if ssize!=None:
            if ssize<0:
                self.__setMaxBufferSize(socket.SO_SNDBUF)
            else:
                self.__sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, ssize)
        if rsize!=None:
            if rsize<0:
                self.__recvspace = self.__setMaxBufferSize(socket.SO_RCVBUF)
            else:
                self.__sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, ssize)

    def getSendBufferSize(self):
        return self.__sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)

    def getReceiveBufferSize(self):
        return self.__sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
    
    # ---------------------------------------------------------------------
                
    def bind(self, addr):
        addr = ip.resolve(addr, self.__sock.family, socket.SOCK_DGRAM)
        if sys.platform!='win32': 
            h = socket.inet_pton(self.__sock.family, addr[0])
        elif self.__sock.family==ip.PF_INET:
            h = socket.inet_aton(addr[0])
        else: h = None
        if h is not None \
                and (self.__sock.family==ip.PF_INET and ip.IN_MULTICAST(h)) \
                or (self.__sock.family==ip.PF_INET6 and ip.IN6_IS_ADDR_MULTICAST(h)):
            if self.__sock.family==ip.PF_INET6:
                level, optname = socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP
            else:
                level, optname = socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP
            self.__sock.setsockopt(level, optname, h+_struct.pack('l', 0))
            self.__sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if hasattr(socket, "SO_REUSEPORT"):
                self.__sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.__sock.bind(addr)
        return self

    def getName(self):
        return self.__sock.getsockname()

    def resolve(self, addr):
        return ip.resolve(addr, self.__sock.family, socket.SOCK_DGRAM)

    def isMulticast(self):
        if sys.platform == 'win32':
            h = socket.inet_aton(self.__sock.getsockname()[0])
        else:
            h = socket.inet_pton(self.__sock.family, self.__sock.getsockname()[0])
        return (self.__sock.family==ip.PF_INET and ip.IN_MULTICAST(h)) or (self.__sock.family==ip.PF_INET6 and ip.IN6_IS_ADDR_MULTICAST(h))

    def __getURL(self, info):
        url = URL()
        url.scheme = "udp"
        url.site.host = info[0]
        url.site.port = info[1]
        return url

    def getURL(self):
        return self.__getURL(self.__sock.getsockname()[:2])
    
    # ---------------------------------------------------------------------
    # Disconnected mode
    
    def sendTo(self, data, addr, resolve=True):
        if resolve: addr = ip.resolve(addr, 
                                      self.__sock.family, 
                                      socket.SOCK_DGRAM)
        return self.__sock.sendto(data, addr)

    def receive(self):
        return self.__sock.recvfrom(self.__recvspace)

    # ---------------------------------------------------------------------
    # Connected mode
    
    def connect(self, addr):
        addr = ip.resolve(addr, self.__sock.family, socket.SOCK_DGRAM)
        self.__sock.connect(addr)
        return self

    def getPeerName(self):
        return self.__sock.getpeername()

    def getPeerURL(self):
        return self.__getURL(self.__sock.getpeername())

    def send(self, data):
        return self.__sock.send(data)

    def disconnect(self):
        try:
            # Connecting to an invalid address disconnects the socket...
            addr = ip.resolve(("",0), self.__sock.family, socket.SOCK_DGRAM)
            self.__sock.connect(addr)
        except socket.error:
            pass

    # ---------------------------------------------------------------------
    # Multicast mode
    
    def setMulticastTTL(self, ttl):
        """1=subnet, 31=site, 64=national, >=127=worldwide"""
        if self.__sock.family==ip.PF_INET6:
            level, optname = socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS
        else:
            level, optname = socket.IPPROTO_IP, socket.IP_MULTICAST_TTL
        self.__sock.setsockopt(level, optname, ttl)
            
    def setMulticastLoopback(self, boolean):
        if self.__sock.family==ip.PF_INET6:
            level, optname = socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP
        else:
            level, optname = socket.IPPROTO_IP, socket.IP_MULTICAST_TTL
        self.__sock.setsockopt(level, optname, 1 if boolean else 0)

# -------------------------------------------------------------------------

def UdpListener(url="udp://:0"):
    if not isinstance(url, URL): url = URL(url)
    family = ip.PF_INET6 if url.site.host.find(':')!=-1 else ip.PF_INET
    s = UdpSocket(family)
    s.bind((url.site.host, url.site.port))
    return s

def UdpSender(url):
    if not isinstance(url, URL): url = URL(url)
    family = ip.PF_INET6 if url.site.host.find(':')!=-1 else ip.PF_INET
    s = UdpSocket(family)
    return s.connect((url.site.host,url.site.port))

def UdpLink(remote, local="udp://:0"):
    if not isinstance(remote, URL): remote = URL(remote)
    s = UdpListener(local)
    s.connect((remote.site.host, remote.site.port))
    return s

# -------------------------------------------------------------------------

if __name__=="__main__":
    u = UdpLink("udp://:7777","udp://:7777")
    u.send(b"hello")
    print(u.receive())
    # FIXME: below...
    #u = UdpListener()
    #u.sendTo(b"hello echo", ("",7)) # echo ?
    #print(u.receive())
