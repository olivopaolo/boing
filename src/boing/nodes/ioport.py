# -*- coding: utf-8 -*-
#
# boing/nodes/ioport.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from PyQt4 import QtCore

from boing.core.MappingEconomy import HierarchicalProducer, HierarchicalConsumer

class DataReader(HierarchicalProducer):
    """It takes an input device and anytime it receives the readyRead
    signal, it reads the device and it produces the obtained data."""
    def __init__(self, inputdevice, postend=True, parent=None):
        super().__init__(parent=parent)
        self.__input = inputdevice
        self.__input.readyRead.connect(self._postData)
        self.postend = postend

    def _postData(self):
        data = self.__input.read()
        if data or self.postend:
            self._postProduct({"str" if self.__input.isTextModeEnabled() \
                                   else "data": data})

    def inputDevice(self):
        return self.__input


class BaseDataWriter(HierarchicalConsumer):
    """It takes an output device and anytime it receives some data from
    a Producer, it writes that data into the output device."""
    def __init__(self, outputdevice, writeend, hz=None):
        super().__init__(request="str" if outputdevice.isTextModeEnabled() \
                             else "data", hz=hz)
        self.__output = outputdevice
        self.writeend = writeend
    
    def _consume(self, products, producer):
        flush = False
        if self.__output.isTextModeEnabled():
            for p in products:
                text = p.get("str")
                if text is not None and (text or self.writeend):
                    self.__output.write(text) ; flush = True
        else:
            for p in products:
                data = p.get("data")
                if data is not None and (data or self.writeend): 
                    self.__output.write(data) ; flush = True
        if flush: self.__output.flush()

    def outputDevice(self):
        return self.__output


class DataWriter(BaseDataWriter, QtCore.QObject):
    
    def __init__(self, outputdevice, writeend=True, hz=None, parent=None):
        QtCore.QObject.__init__(self, parent)
        BaseDataWriter.__init__(self, outputdevice, writeend, hz)


class DataIO(DataReader, BaseDataWriter):

    def __init__(self, inputdevice, outputdevice, hz=None, parent=None):
        DataReader.__init__(self, inputdevice, parent)
        BaseDataWriter.__init__(self, outputdevice, hz)

    def __del__(self):
        DataReader.__del__(self)
        BaseDataWriter.__del__(self)

    def _checkRef(self):
        DataReader._checkRef(self)
        BaseDataWriter._checkRef(self)

# -------------------------------------------------------------------

'''class DeviceNode(Node):

    def __init__(self, textmode=False, parent=None):
        Node.__init__(self, request="data" if not textmode else "str",
                      parent=parent)
        self.__textModeEnabled = textmode
        self.__outputbuffer = io.BytesIO() if not textmode \
            else io.StringIO()

    def isTextModeEnabled(self):
        return self.__textModeEnabled

    def bytesToWrite(self):
        return 0

    def flush(self):
        

    def read(self, size=io.DEFAULT_BUFFER_SIZE):
        data = self.__fd.read(size) if not self.__isatty else self.__fd.readline(size)
        return data

    def readLine(self, limit=-1):
        return self.__fd.readline(limit)

    def readAll(self):
        return self.__fd.readall()

    def write(self, data):
        n = self.__fd.write(data)
        if n: self.bytesWritten.emit(n)
        return n'''
