# -*- coding: utf-8 -*-
#
# boing/osc/OscEndpoint.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from PyQt4 import QtCore

from boing import osc
from boing.eventloop.ProducerConsumer import Producer

class OscEndpoint(Producer):

    # trigger signal
    packetReady = QtCore.pyqtSignal(QtCore.QObject)

    def __init__(self, socket, parent=None):
        super().__init__(parent)
        self.__socket = socket
        self.__socket.readyRead.connect(self.__decodeData)
    
    def url(self):
        url = self.__socket.url()
        url.scheme = "osc."+url.scheme
        return url

    # ---------------------------------------------------------------------
    # Disconnected mode
    def sendTo(self, packet, addr):
        self.__socket.sendTo(packet.encode(), addr)

    # ---------------------------------------------------------------------
    # Connected mode
    def send(self, packet):
        self.__socket.send(packet.encode())

    def __decodeData(self):
        data, source = self.__socket.receiveFrom()
        self._postProduct(osc.decode(data, "osc://%s:%s"%source))


# -----------------------------------------------------------------

if __name__=="__main__":
    import sys
    from boing.eventloop.EventLoop import EventLoop
    from boing.eventloop.ProducerConsumer import Consumer
    from boing.udp.UdpSocket import UdpListener
    class DumpConsumer(Consumer):
        def __init__(self, hz=None):
            super().__init__(hz)
        def _consume(self, products, producer):
            for p in products:
                if isinstance(p, osc.Packet):
                    p.debug(sys.stdout)
    endpoint = OscEndpoint(UdpListener("udp://127.0.0.1:3333"))
    consumer = DumpConsumer()
    consumer.subscribeTo(endpoint)
    print("Listening at", endpoint.url())
    EventLoop.run()
    del endpoint    


