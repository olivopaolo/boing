# -*- coding: utf-8 -*-
#
# boing/utils/TextIO.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections

from boing.eventloop.MappingEconomy import Node


'''class TextReader(DataReader):

    def __init__(self, inputdevice, encoding="utf-8", parent=None):
        DataReader.__init__(self, inputdevice, parent)
        self.encoding = encoding
        
    def _postData(self):
        data = self.inputDevice().read()        
        self._postProduct(ExtensibleStruct(data=data.encode(self.encoding)))


class TextWriter(DataWriter):

    def __init__(self, outputdevice, encoding="utf-8", parent=None):
        DataWriter.__init__(self, outputdevice, parent)
        self.encoding = encoding
        self.errors = "replace"

    def _consume(self, products, producer):
        for p in products:
            if isinstance(p, collections.Mapping) and "data" in p: 
                data = p["data"]
                if data: 
                    out = self.outputDevice()
                    out.write(data.decode(self.encoding, self.errors))
                    out.flush()'''

class TextEncoder(Node):
    
    def __init__(self, encoding="utf-8", hz=None, parent=None):
        # FIXME: set productoffer
        Node.__init__(self, request="str", hz=hz, parent=parent)
        self.encoding = encoding

    def _consume(self, products, producer):
        for p in products:
            if "str" in p: 
                text = p["str"]
                if text is not None: 
                    self._postProduct({"data":text.encode(self.encoding)})


class TextDecoder(Node):
    
    def __init__(self, encoding="utf-8", hz=None, parent=None):
        # FIXME: set productoffer
        Node.__init__(self, request="data", hz=hz, parent=parent)
        self.encoding = encoding
        self.errors = "replace"

    def _consume(self, products, producer):
        for p in products:
            if "data" in p:
                data = p["data"]
                if data is not None: 
                    text = data.decode(self.encoding, self.errors)
                    product = {"str": text}
                    self._postProduct(product)
