# -*- coding: utf-8 -*-
#
# boing/utils/TextIO.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from boing.utils.ExtensibleStruct import ExtensibleStruct
from boing.utils.DataIO import DataWriter, DataReader

class TextReader(DataReader):

    def __init__(self, inputdevice, encoding="utf-8", parent=None):
        DataReader.__init__(self, inputdevice, parent)
        self.encoding = encoding
        
    def _postData(self):
        data = self.inputDevice().read()        
        self._postProduct(ExtensibleStruct(data=data.encode(self.encoding)))


class TextWriter(DataWriter):

    def __init__(self, outputdevice, encoding="utf-8"):
        DataWriter.__init__(self, outputdevice)
        self.encoding = encoding
        self.errors = "replace"

    def _consume(self, products, producer):
        for p in products:
            if isinstance(p, ExtensibleStruct): 
                data = p.get("data")
                if data: 
                    out = self.outputDevice()
                    out.write(data.decode(self.encoding, self.errors))
                    out.flush()
