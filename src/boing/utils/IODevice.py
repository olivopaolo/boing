# -*- coding: utf-8 -*-
#
# boing/utils/IODevice.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import io
import weakref

from PyQt4.QtCore import QObject, pyqtSignal

from boing.eventloop.EventLoop import EventLoop

class IODevice(QObject):
    """Class for wrapping a generic file descriptor, like a file,
    the stdin or the stdout."""
    
    # Open mode
    ReadOnly = 0x01
    WriteOnly = 0x02
    ReadWrite = 0x03
    Append = 0x04

    # Signals
    bytesWritten = pyqtSignal(int)
    aboutToClose = pyqtSignal()

    def __init__(self, fd, parent=None):
        QObject.__init__(self, parent)
        self.__fd = fd
        self.__isatty = fd.isatty() if hasattr(fd, "isatty") else False

    def fd(self):
        return self.__fd

    def isOpen(self):
        return not self.__fd.closed

    def bytesToWrite(self):
        return 0

    def flush(self):
        if hasattr(self.__fd, "flush"): self.__fd.flush()

    def close(self):
        self.aboutToClose.emit()
        self.__fd.close()

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
        return n

    def seek(self, offset, whence=io.SEEK_SET):
        self.__fd.seek(offset, whence)


class CommunicationDevice(IODevice):
    """Specific class for devices for which the readyRead signal is
    usefull like Unix not regular files and stdin. TcpSocket and
    UdpSocket do not inherit this class because they inherit specific
    Qt classes."""
    
    readyRead = pyqtSignal()

    def __init__(self, fd, parent=None):
        IODevice.__init__(self, fd, parent)
        EventLoop.if_readable(self.fd(), CommunicationDevice._emitReadyRead,
                              weakref.ref(self))
        
    def _emitReadyRead(did, ref):
        device = ref()
        if device is None: EventLoop.cancel_fdhandler(did)
        else: device.readyRead.emit()

        

    
