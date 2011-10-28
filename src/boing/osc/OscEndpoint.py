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
from boing.utils.ExtensibleStruct import ExtensibleStruct
from boing.utils.SocketEndpoint import SocketEndpoint

class OscEndpoint(SocketEndpoint):

    def __init__(self, socket, parent=None):
        SocketEndpoint.__init__(self, socket, parent=parent)

    def _decodeData(self):
        data, source = self._socket.receiveFrom()
        packet = osc.decode(data, "osc://%s:%s"%source)
        self._postProduct(ExtensibleStruct(osc=packet, data=data))

    def _consume(self, products, producer):
        for p in products:
            if isinstance(p, ExtensibleStruct):                 
                packet = p.get("osc")
                if packet is not None: 
                    data = p.get("data")
                    if data is not None: 
                        self._socket.send(data)
                    else:
                        self._socket.send(packet.encode())


# -----------------------------------------------------------------

if __name__=="__main__":
    import sys
    from boing.eventloop.EventLoop import EventLoop
    from boing.eventloop.ProducerConsumer import Consumer
    from boing.udp.UdpSocket import UdpListener
    class DumpConsumer(Consumer):
        def __init__(self, hz=None):
            Consumer.__init__(self, hz)
        def _consume(self, products, producer):
            for p in products:
                if isinstance(p, ExtensibleStruct):                 
                    packet = p.get("osc")
                    if packet is not None: packet.debug(sys.stdout)
    endpoint = OscEndpoint(UdpListener("udp://127.0.0.1:3333"))
    consumer = DumpConsumer()
    consumer.subscribeTo(endpoint)
    print("Listening at", endpoint.socket().url())
    EventLoop.run()
    del endpoint    


