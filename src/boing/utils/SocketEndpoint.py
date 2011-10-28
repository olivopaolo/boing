# -*- coding: utf-8 -*-
#
# boing/utils/SocketEndpoint.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from PyQt4 import QtCore

from boing.utils.ExtensibleStruct import ExtensibleStruct
from boing.eventloop.ProducerConsumer import Producer, Consumer

class SocketEndpoint(Producer, Consumer):

    def __init__(self, socket, parent=None):
        Producer.__init__(self, parent)
        Consumer.__init__(self, parent=parent)
        self._socket = socket
        self._socket.readyRead.connect(self._decodeData)    

    def _decodeData(self):
        data, source = self._socket.receiveFrom()
        self._postProduct(ExtensibleStruct(data=data))

    def _consume(self, products, producer):
        for p in products:
            if isinstance(p, ExtensibleStruct): 
                data = p.get("data")
                if data is not None: self._socket.send(data)

    def _checkRef(self):
        Producer._checkRef(self)
        Consumer._checkRef(self)
        
    def socket(self):
        return self._socket

# -----------------------------------------------------------------

if __name__=="__main__":
    import sys
    from boing.eventloop.EventLoop import EventLoop
    from boing.udp.UdpSocket import UdpListener
    class DumpConsumer(Consumer):
        def _consume(self, products, producer):
            for p in products:
                data = p.get("data")
                if data is not None: print(data.decode())
    endpoint = SocketEndpoint(UdpListener("udp://:7777"))
    consumer = DumpConsumer()
    consumer.subscribeTo(endpoint)
    print("Listening at", endpoint.socket().url())
    EventLoop.run()
    del endpoint    


