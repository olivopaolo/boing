# -*- coding: utf-8 -*-
#
# boing/utils/DataIO.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from boing.utils.ExtensibleStruct import ExtensibleStruct
from boing.eventloop.ProducerConsumer import Producer, Consumer

class DataReader(Producer):

    def __init__(self, inputdevice, parent=None):
        Producer.__init__(self, parent)
        self.__in = inputdevice
        self.__in.readyRead.connect(self._postData)

    def _postData(self):
        data = self.__in.read()
        self._postProduct(ExtensibleStruct(data=data))

    def inputDevice(self):
        return self.__in


class DataWriter(Consumer):

    def __init__(self, outputdevice, parent=None):
        Consumer.__init__(self, parent=parent)
        self.__out = outputdevice

    def _consume(self, products, producer):
        for p in products:
            if isinstance(p, ExtensibleStruct): 
                data = p.get("data")
                if data: 
                    self.__out.write(data)
                    self.__out.flush()

    def outputDevice(self):
        return self.__out
