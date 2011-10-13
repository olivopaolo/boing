# -*- coding: utf-8 -*-
#
# boing/tcp/EchoServer.py -
#
# Authors: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import logging

from boing import ip
from boing.eventloop.EventLoop import EventLoop
from boing.tcp.TcpServer import TcpServer
from boing.tcp.TcpSocket import TcpSocket


class EchoServer(TcpServer):

    class EchoSocket(TcpSocket):

        def __init__(self, family=ip.PF_INET, socket=None, options=tuple()):
            super().__init__(family, socket, options)
            self.logger = logging.getLogger("EchoSocket.%d"%id(self))
            if socket is not None:
                self.logger.debug("New client: %s"%str(self.peername()))

    def __init__(self, port=0, host=None, backlog=10, 
                 family=None, options=tuple()):
        super().__init__(port, host, backlog, family, options, 
                         EchoServer.__newclient, EchoServer.EchoSocket)
        self.logger = logging.getLogger("EchoServer.%d"%id(self))
       
    @staticmethod
    def __newclient(client):
        EventLoop.if_readable(client, 
                              EchoServer.__client_listener, 
                              client)

    @staticmethod
    def __client_listener(did, client):
        data = client.receive()
        if data: 
            client.logger.debug("%s: %s"%(str(client.peername()),
                                          data))
            client.send(data)
        else:
            client.logger.debug("Connection closed: %s"%str(client.peername()))
            client.close()
            EventLoop.cancel_fdhandler(did)

# -------------------------------------------------------------------

if __name__=="__main__":
    logging.basicConfig(level=logging.getLevelName("DEBUG"))
    server = EchoServer(5555)
    print("EchoServer listening at", server.url())
    EventLoop.run()
    del server
