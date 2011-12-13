# -*- coding: utf-8 -*-
#
# boing/utils/DataIO.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections

from PyQt4.QtCore import QObject

from boing.utils.ExtensibleTree import ExtensibleTree
from boing.eventloop.ProducerConsumer import Producer, Consumer

class DataReader(Producer):
    """It takes an input device and anytime it receives the readyRead
    signal, it reads the device and it produces the obtained data."""

    def __init__(self, inputdevice, parent=None):
        Producer.__init__(self, parent)
        self.__in = inputdevice
        self.__in.readyRead.connect(self._postData)

    def _postData(self):
        data = self.__in.read()
        self._postProduct(ExtensibleTree({"data":data}))

    def inputDevice(self):
        return self.__in


class DataWriter(QObject, Consumer):
    """It takes an output device and anytime it receives some data from
    a Producer, it writes that data into the output device."""

    def __init__(self, outputdevice, parent=None):
        QObject.__init__(self, parent)
        Consumer.__init__(self)
        self.__out = outputdevice

    def _consume(self, products, producer):
        for p in products:
            if isinstance(p, collections.Mapping) and "data" in p: 
                data = p["data"]
                if data: 
                    self.__out.write(data)
                    self.__out.flush()

    def outputDevice(self):
        return self.__out
