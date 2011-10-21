# -*- coding: utf-8 -*-
#
# boing/tcp/EchoServer.py -
#
# Authors: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import logging

from PyQt4.QtNetwork import QAbstractSocket, QHostAddress

from boing.tcp.TcpSocket import TcpSocket
from boing.tcp.TcpServer import TcpServer

class EchoSocket(TcpSocket):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger("EchoSocket.%d"%id(self))
        self.readyRead.connect(self.__echoData)
        self.disconnected.connect(self.__disconnected)

    def setSocketDescriptor(self, descriptor):
        super().setSocketDescriptor(descriptor)
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
    from boing.eventloop.EventLoop import EventLoop
    logging.basicConfig(level=logging.getLevelName("DEBUG"))
    server = EchoServer()
    print("EchoServer listening at", server.url())
    EventLoop.run()
    del server
