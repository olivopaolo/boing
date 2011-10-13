# -*- coding: utf-8 -*-
#
# boing/tcp/TcpSocket.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import errno
import os
import socket as _socket
import sys

from boing import ip
from boing.url import URL

class TcpSocket(object):

    def __init__(self, family=ip.PF_INET, socket=None, options=tuple()):
        if isinstance(socket, _socket.socket): self.__sock = socket
        elif family not in (ip.PF_INET, ip.PF_INET6):
            raise ValueError("Unsupported protocol family (use PF_INET or PF_INET6)")
        else: self.__sock = _socket.socket(family, _socket.SOCK_STREAM, 0)
        self.__setoption(options)
        
    def __del__(self):
        if self.__autoclose: self.close()

    def __setoption(self, options):
        self.__autoclose = "autoclose" in options
        if "nodelay" in options:
            #print "TCP_NODELAY", self
            self.__sock.setsockopt(_socket.IPPROTO_TCP, _socket.TCP_NODELAY, 1)
        if "fastack" in options and hasattr(_socket, "TCP_FASTACK"):
            #print "TCP_FASTACK", self
            self.__sock.setsockopt(_socket.IPPROTO_TCP, _socket.TCP_FASTACK, 1)
        if "nosigpipe" in options:
            if hasattr(_socket, "SO_NOSIGPIPE"):
                sock.setsockopt(_socket.SOL_SOCKET, _socket.SO_NOSIGPIPE, 1)
            elif sys.platform == 'win32': pass
            else:
                import signal
                signal.signal(signal.SIGPIPE, signal.SIG_IGN)

    def connect(self, addr, options=[]):
        addr = ip.resolve(addr, self.__sock.family, _socket.SOCK_STREAM)
        error = self.__sock.connect_ex(addr)
        if error!=0:
            if error==errno.EINPROGRESS:
                # FIXME: should wait until socket is writable
                print("EINPROGRESS!",addr)
            else: raise _socket.error((error, os.strerror(error), addr))
        return self

    def send(self, data):
        # FIXME: don't trust WAITALL, loop until all data has been sent?
        #return self.__sock.send(data, _socket.MSG_WAITALL)
        return self.__sock.send(data)

    def receive(self, size=4096, waitall=False):
        if waitall:
            # FIXME: don't trust WAITALL, loop until all data has been sent?
            return self.__sock.recv(size, _socket.MSG_WAITALL)
        else:
            return self.__sock.recv(size)
    
    def close(self):
        try: self.__sock.shutdown(_socket.SHUT_RDWR)
        except Exception: pass
        self.__sock.close()

    def fileno(self):        
        """Return the socket's file descriptor."""
        return self.__sock.fileno()

    def name(self):
        """Return the socket’s own address:
        - (host, port) for the AF_INET address family;
        - (host, port, flowinfo, scopeid) for the AF_INET6 address family."""
        return self.__sock.getsockname()

    def peername(self):
        """Return the remote address to which the socket is connected."""
        return self.__sock.getpeername()

    def peerurl(self):
        """Return the remote URL to which the socket is connected."""
        url = URL()
        url.scheme = "tcp"
        url.site.host, url.site.port = self.__sock.getpeername()[:2]
        return url

    def socket(self):
        """Return low level python socket."""
        return self.__sock

    def url(self):
        """Return the socket's URL, i.e. tcp://<host>:<port>."""
        url = URL()
        url.scheme = "tcp"
        url.site.host, url.site.port = self.__sock.getsockname()[:2]
        return url
    
# -------------------------------------------------------------------------

def TcpConnection(url, options=tuple()):
    if not isinstance(url, URL): url = URL(url)
    family = ip.PF_INET6 if url.site.host.find(':')!=-1 else ip.PF_INET
    socket = TcpSocket(family, options=options)
    socket.connect((url.site.host,url.site.port))
    return socket

# -------------------------------------------------------------------------

if __name__=="__main__":
    import sys, traceback
    try: url = URL(sys.argv[1])
    except: 
        traceback.print_exc()
        url = URL("http://127.0.0.1:80")
    c = TcpConnection(url)
    data = "HEAD %s HTTP/1.0\n\n"%url.path
    c.send(data.encode())
    print(c.receive())
    c.close()

