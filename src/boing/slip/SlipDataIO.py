# -*- coding: utf-8 -*-
#
# boing/slip/SlipDataIO.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from boing import slip
from boing.utils.DataIO import DataWriter, DataReader
from boing.utils.ExtensibleStruct import ExtensibleStruct

class SlipDataReader(DataReader):
    """The SlipDataReader espects from its input device slip encoded
    data, that it will decode and post as a data product."""

    def __init__(self, inputdevice, parent=None):
        DataReader.__init__(self, inputdevice, parent)
        self.__slipbuffer = None

    def _postData(self):
        encoded = self.inputDevice().read()
        if encoded:
            packets, self.__slipbuffer = slip.decode(encoded, self.__slipbuffer)
            for packet in packets:
                self._postProduct(ExtensibleStruct(data=packet))
        else: self._postProduct(ExtensibleStruct(data=bytes()))


class SlipDataWriter(DataWriter):
    """The SlipDataWriter encodes using slip the received data prior
    to write it into the output file."""

    def __init__(self, outputdevice):
        DataWriter.__init__(self, outputdevice)

    def _consume(self, products, producer):
        for p in products:
            if isinstance(p, ExtensibleStruct): 
                data = p.get("data")
                if data:
                    out = self.outputDevice()
                    out.write(slip.encode(data))
                    out.flush()
