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
import weakref

from boing import ip
from boing.eventloop.EventLoop import EventLoop
from boing.tcp.TcpSocket import TcpSocket
from boing.url import URL

class TcpServer(object):

    def __init__(self, port=0, host=None, backlog=10, 
                 family=None, options=[],
                 delegate=None, factory=TcpSocket):
        if family is None:
            if host is None or ":" not in host: family = ip.PF_INET
            else: family = ip.PF_INET6
        elif family not in (ip.PF_INET, ip.PF_INET6):
            raise ValueError("Unsupported protocol family (use PF_INET or PF_INET6)")
        self.__sock = _socket.socket(family, _socket.SOCK_STREAM, 0)
        self.__setoptions(options)
        if host is not None: addr = ip.resolve((host, port), 
                                               family, _socket.SOCK_STREAM)
        else: addr = ip.resolve((_socket.getfqdn(), port), 
                                family, _socket.SOCK_STREAM)
        self.__sock.bind(addr)
        self.__sock.listen(backlog)
        self.__factory = factory
        self.__delegate = delegate if delegate is not None \
            else lambda client: client.close()
        self.__did = EventLoop.if_readable(self.__sock, 
                                           TcpServer.__newclient,
                                           weakref.ref(self))

    def __del__(self):
        self.__sock.shutdown(_socket.SHUT_RDWR)
        self.__sock.close()

    def __setoptions(self, options):
        if "nodelay" in options:
            self.__sock.setsockopt(_socket.IPPROTO_TCP, _socket.TCP_NODELAY, 1)
        if "fastack" in options and hasattr(_socket, "TCP_FASTACK"):
            self.__sock.setsockopt(_socket.IPPROTO_TCP, _socket.TCP_FASTACK, 1)
        if "reuse" in options:
            # so we can restart the server later without having to
            # wait for the system to release the port
            if hasattr(_socket, "SO_REUSEPORT"):
                self.__sock.setsockopt(_socket.SOL_SOCKET, 
                                       _socket.SO_REUSEPORT, 1)
            self.__sock.setsockopt(_socket.SOL_SOCKET, 
                                   _socket.SO_REUSEADDR, 1)
        if "nosigpipe" in options:
            if hasattr(_socket, "SO_NOSIGPIPE"):
                self.__sock.setsockopt(_socket.SOL_SOCKET, 
                                       _socket.SO_NOSIGPIPE, 1)
            else:
                import signal as _signal
                if hasattr(_signal, "SIGPIPE"):
                    _signal.signal(_signal.SIGPIPE, _signal.SIG_IGN)
            
    @property
    def factory(self):
        return self.__factory

    @property
    def delegate(self):
        return self.__delegate

    def fileno(self):
        """Return the socket's file descriptor."""
        return self.__sock.fileno()

    def name(self):
        """Return the socket’s own address:
        - (host, port) for the AF_INET address family;
        - (host, port, flowinfo, scopeid) for the AF_INET6 address family."""
        return self.__sock.getsockname()

    def socket(self):
        """Return low level python socket."""
        return self.__sock

    def url(self):
        """Return the socket's URL, i.e. tcp://<host>:<port>."""
        url = URL()
        url.scheme = "tcp"
        url.site.host, url.site.port = self.__sock.getsockname()[:2]
        return url

    @staticmethod
    def __newclient(did, ref):
        server = ref()
        if server is None: EventLoop.cancel_fdhandler(did)
        else:
            conn, addr = server.socket().accept()
            socket = server.factory(socket=conn)
            server.delegate(socket)

# -------------------------------------------------------------------

if __name__=="__main__":
    import datetime
    import traceback
    def newClient(connection):
        client = connection.name()
        peer = connection.peername()
        #print client, peer, (peer[1], client[1])
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
    server = TcpServer(5555, 
                       #options=("nodelay","fastack","reuse","nosigpipe"), 
                       delegate=newClient)
    print(ip.getProtocolFamilyName(server.socket().family), 
          server.name(), server.url())
    EventLoop.run()
    del server
