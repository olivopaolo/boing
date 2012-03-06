# -*- coding: utf-8 -*-
#
# boing/slip/SlipDataIO.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections

from boing import slip

from boing.eventloop.MappingEconomy import Node

'''class SlipDataReader(DataReader):
    """The SlipDataReader espects from its input device slip encoded
    data, that it will decode and post as a data product."""

    def __init__(self, inputdevice, parent=None):
        DataReader.__init__(self, inputdevice, parent)
        self._slipbuffer = None

    def _postData(self):
        encoded = self.inputDevice().read()
        if encoded:
            packets, self._slipbuffer = slip.decode(encoded, self._slipbuffer)
            for packet in packets:
                self._postProduct(ExtensibleTree({"data":packet}))
        else: 
            self._postProduct(ExtensibleTree({"data":bytes()}))


class SlipDataWriter(DataWriter):
    """The SlipDataWriter encodes using slip the received data prior
    to write it into the output file."""

    def __init__(self, outputdevice, parent=None):
        DataWriter.__init__(self, outputdevice, parent)

    def _consume(self, products, producer):
        for p in products:
            if isinstance(p, collections.Mapping) and "data" in p: 
                data = p["data"]
                if data:
                    out = self.outputDevice()
                    out.write(slip.encode(data))
                    out.flush()'''


class SlipEncoder(Node):
    # FIXME: The slip encoder should be able to get slip products also
    # but if I let it do it, it will forward the same data
    # twice. subscription on request using productoffer

    def __init__(self, hz=None, parent=None):
        #FIXME: set productoffer
        Node.__init__(self, request="data", hz=hz, parent=parent)
        self._addTag("data", {"data":bytearray()}, update=False)

    def _consume(self, products, producer):
        
        if self._tag("data"):
            for p in products:
                packet = p.get("data")
                if packet is not None:
                    if packet:
                        self._postProduct({'data': slip.encode(packet)})
                    else:
                        self._postProduct({'data': bytearray()})
                    

class SlipDecoder(Node):
    
    def __init__(self, hz=None, parent=None):
        # FIXME: set productoffer
        Node.__init__(self, request="data", hz=hz, parent=parent)
        self._slipbuffer = None
        self._addTag("data", {"data":bytearray()}, update=False)
        self._addTag("slip", {"slip":bytearray()}, update=False)
        # FIXME: if request changes it is possible that the slip
        # buffer is not updated and data may be loss. Add notification.

    def _consume(self, products, producer):
        if self._tag("data") or self._tag("slip"):
            for p in products:
                encoded = p.get("data")
                if encoded is not None:
                    if self._tag("slip"): self._postProduct({"slip": encoded})
                    if self._tag("data"):
                        if encoded:
                            packets, self._slipbuffer = slip.decode(encoded, 
                                                                    self._slipbuffer)
                            for packet in packets:
                                self._postProduct({"data":packet})
                        else: 
                            self._postProduct({"data":bytearray()})
