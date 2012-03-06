# -*- coding: utf-8 -*-
#
# boing/json/encoding.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import json

from PyQt4 import QtCore 

import boing.json
from boing.eventloop.MappingEconomy import Node
from boing.eventloop.OnDemandProduction import OnDemandProducer

class JSONEncoder(Node):
    """Encode received products using JSON protocol."""
    def __init__(self, requests=OnDemandProducer.ANY_PRODUCT, 
                 hz=None, parent=None):
        #FIXME: set productoffer
        Node.__init__(self, request=request, hz=hz, parent=parent)
        self._addTag("str", {"str":str()}, update=False)
        self._addTag("data", {"data":bytearray()}, update=False)

    def _consume(self, products, producer):
        for p in products:
            try:
                jsoncode = json.dumps(p, cls=boing.json.ProductEncoder, 
                                      separators=(',',':'))
            except TypeError:
                pass
            else:
                product = {}
                if self._addTag("str"): product["str"] = jsoncode
                if self._addTag("data"): product["data"] = jsoncode.encode() 
                self._postProduct(product)


class JSONDecoder(Node):
    """Decode received JSON strings to python objects and post them as
    products."""
    def __init__(self, hz=None, parent=None):
        Node.__init__(self, request="str", hz=hz, parent=parent)

    def _consume(self, products, producer):
        for p in products:            
            jsoncode = p.get("str")
            if jsoncode:
                decoded = json.loads(jsoncode, 
                                      object_hook=boing.json.productHook)
                self._postProduct(decoded)
