# -*- coding: utf-8 -*-
#
# boing/utils/DataIO.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections

from PyQt4 import QtCore

from boing.eventloop.MappingEconomy import HierarchicalProducer, HierarchicalConsumer

class DataReader(HierarchicalProducer):
    """It takes an input device and anytime it receives the readyRead
    signal, it reads the device and it produces the obtained data."""
    def __init__(self, inputdevice, parent=None):
        #FIXME: set productoffer
        HierarchicalProducer.__init__(self, parent=parent)
        self.__in = inputdevice
        self.__istextbased = inputdevice.isTextModeEnabled()
        self.__in.readyRead.connect(self._postData)

    def _postData(self):
        data = self.__in.read()
        self._postProduct({"data" if not self.__istextbased else "str": data})

    def inputDevice(self):
        return self.__in


class BaseDataWriter(HierarchicalConsumer):
    """It takes an output device and anytime it receives some data from
    a Producer, it writes that data into the output device."""
    def __init__(self, outputdevice, hz=None):
        self.__istextbased = outputdevice.isTextModeEnabled()
        HierarchicalConsumer.__init__(self, 
                                      "data" if not self.__istextbased \
                                          else "str", hz)
        self.__out = outputdevice
        self.__buffer = []
    
    def _consume(self, products, producer):
        flush = False
        if self.__istextbased:
            for p in products:
                text = p.get("str")
                if text is not None: self.__out.write(text) ; flush = True
        else:
            for p in products:
                data = p.get("data")
                if data is not None: self.__out.write(data) ; flush = True
        if flush: self.__out.flush()

    def outputDevice(self):
        return self.__out


class DataWriter(BaseDataWriter, QtCore.QObject):
    
    def __init__(self, outputdevice, hz=None, parent=None):
        QtCore.QObject.__init__(self, parent)
        BaseDataWriter.__init__(self, outputdevice, hz)


class DataIO(DataReader, BaseDataWriter):

    def __init__(self, device, hz=None, parent=None):
        DataReader.__init__(self, device, parent)
        BaseDataWriter.__init__(self, device, hz)

    def __del__(self):
        DataReader.__del__(self)
        BaseDataWriter.__del__(self)

    def _checkRef(self):
        DataReader._checkRef(self)
        BaseDataWriter._checkRef(self)
