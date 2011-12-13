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
from boing.utils.DataIO import DataWriter, DataReader
from boing.utils.ExtensibleTree import ExtensibleTree

class SlipDataReader(DataReader):
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
                    out.flush()
