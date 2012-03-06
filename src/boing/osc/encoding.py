# -*- coding: utf-8 -*-
#
# boing/osc/encoding.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import io

from boing import osc
from boing.eventloop.MappingEconomy import Node

class OscEncoder(Node):

    def __init__(self, hz=None, parent=None):
        #FIXME: set productoffer
        Node.__init__(self, request="osc", hz=hz, parent=parent)
        self._addTag("data", {"data":bytearray()}, update=False)

    def _consume(self, products, producer):
        if self._tag("data"):
            for p in products:
                packet = p.get("osc")
                if packet is not None:
                    self._postProduct({'data': packet.encode()})


class OscDecoder(Node):

    def __init__(self, hz=None, parent=None):
        #FIXME: set productoffer
        Node.__init__(self, request="data", hz=hz, parent=parent)
        self._addTag("osc", {"osc":osc.Packet()}, update=False)

    def _consume(self, products, producer):
        if self._tag("osc"):
            for p in products:
                data = p.get("data")
                if data:
                    packet = osc.decode(data)
                    self._postProduct({'osc':packet})


class OscDebug(Node):

    def __init__(self, hz=None, parent=None):
        #FIXME: set productoffer
        Node.__init__(self, request="osc", hz=hz, parent=parent)
        self._addTag("str", {"str": str()})

    def _consume(self, products, producer):
        if self._tag("str"):
            for p in products:
                packet = p.get("osc")
                if packet is not None:
                    stream = io.StringIO()
                    packet.debug(stream)
                    self._postProduct({'str':stream.getvalue()})
