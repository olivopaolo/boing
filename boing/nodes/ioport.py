# -*- coding: utf-8 -*-
#
# boing/nodes/ioport.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from PyQt4 import QtCore

from boing import Offer, QRequest, Producer, Consumer
from boing.utils import assertIsInstance, quickdict

class DataReader(Producer):
    """It takes an input device and anytime it receives the readyRead
    signal, it reads the device and it produces the obtained data."""
    def __init__(self, inputdevice, postend=True, parent=None):
        self._textmode = inputdevice.isTextModeEnabled()
        if self._textmode:
            offer = Offer(quickdict(str=str()))
            tags = dict(str=QRequest("str"))
        else:
            offer = Offer(quickdict(data=bytearray()))
            tags = dict(data=QRequest("data"))
        super().__init__(offer, tags=tags, parent=parent)
        self.__input = inputdevice
        self.__input.readyRead.connect(self._postData)
        self.postend = assertIsInstance(postend, bool)

    def _postData(self):        
        data = self.__input.read()
        attr = "str" if self._textmode else "data"
        if attr in self._activetags and (data or self.postend):
            product = quickdict()
            product[attr] = data
            self.postProduct(product)

    def inputDevice(self):
        return self.__input


class DataWriter(Consumer):
    """It takes an output device and anytime it receives some data from
    a Producer, it writes that data into the output device."""
    def __init__(self, outputdevice, writeend=True, hz=None, parent=None):
        self._textmode = outputdevice.isTextModeEnabled()
        super().__init__(request=QRequest("str" if self._textmode else "data"),
                         hz=hz, parent=parent)
        self.__output = outputdevice
        self.writeend = assertIsInstance(writeend, bool)
    
    def _consume(self, products, producer):
        flush = False
        attr = "str" if self._textmode else "data"
        for product in products:
            if attr in product:
                value = product[attr]
                if value or self.writeend:
                    self.__output.write(value) ; flush = True
        if flush: self.__output.flush()

    def outputDevice(self):
        return self.__output


'''class DataIO(DataReader, _BaseDataWriter):

    def __init__(self, inputdevice, outputdevice, hz=None, parent=None):
        DataReader.__init__(self, inputdevice, parent)
        _BaseDataWriter.__init__(self, outputdevice, hz)

    def __del__(self):
        DataReader.__del__(self)
        _BaseDataWriter.__del__(self)

    def _checkRefs(self):
        DataReader._checkRefs(self)
        _BaseDataWriter._checkRefs(self)'''
