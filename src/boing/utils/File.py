# -*- coding: utf-8 -*-
#
# boing/utils/File.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import os
import weakref

from PyQt4.QtCore import Qt, QObject, QFileInfo, pyqtSignal

from boing.eventloop.EventLoop import EventLoop
from boing.utils.IODevice import IODevice, CommunicationDevice
from boing.url import URL

def openFile(filepath, mode=IODevice.ReadOnly, uncompress=False):
    """Open a file and return its file descriptor. If 'uncompress' is
    True and 'filepath' points to a compressed archive, the
    correspondent python module will be used to obtain the file
    descriptor."""
    if mode&IODevice.ReadOnly:
        if mode&IODevice.Append: pymode = "r+b"
        elif mode&IODevice.WriteOnly: pymode = "w+b"
        else: pymode = "rb"      
    elif mode&IODevice.Append: pymode = "ab"
    else: pymode = "wb"
    if os.path.splitext(filepath)[1]==".bz2" \
            and (uncompress or mode&IODevice.WriteOnly or mode&IODevice.Append):
        import bz2
        return bz2.BZ2File(filepath, pymode, 0)
    else:
        return open(filepath, pymode, 0)


class BaseFile(object):
    """BaseFile defines a set of common methods that any file should have.""" 

    def __init__(self, url):
        if not isinstance(url, URL): url = URL(str(url))
        self._fileinfo = QFileInfo(str(url.path))

    def absoluteDir(self):
        return str(self._fileinfo.absoluteDir())

    def absoluteFilePath(self):
        return str(self._fileinfo.absoluteFilePath())

    def fileName(self):
        return str(self._fileinfo.fileName())

    def url(self):
        """Return the file's URL, i.e. file://<file-path>."""
        return URL("file://%s"%self._fileinfo.absoluteFilePath())


class File(BaseFile, IODevice):
    
    def __init__(self, url, mode=IODevice.ReadOnly,
                 uncompress=False, parent=None):
        BaseFile.__init__(self, url)
        fd = openFile(self.absoluteFilePath(), mode, uncompress)
        IODevice.__init__(self, fd, parent)


class CommunicationFile(BaseFile, CommunicationDevice):

    def __init__(self, url, mode=IODevice.ReadOnly, 
                 uncompress=False, parent=None):
        BaseFile.__init__(self, url)
        fd = openFile(self.absoluteFilePath(), mode, uncompress)
        CommunicationDevice.__init__(self, fd, parent)

# -------------------------------------------------------------------------

class FileReader(File):
    """The FileReader can be used to read regular files along the
    EventLoop. When the 'start' method is invoked, the FileReader will
    trigger the readyRead signal and it will repeat it every time the
    read method is invoked."""

    readyRead = pyqtSignal()
    completed = pyqtSignal()
    __read = pyqtSignal()

    def __init__(self, url, mode=IODevice.ReadOnly, 
                 uncompress=False, parent=None):
        File.__init__(self, url, mode, uncompress, parent)
        self._atend = False
        self.__read.connect(self._emitReadyRead, Qt.QueuedConnection)
        
    def atEnd(self):
        return self._atend

    def start(self):
        self.__read.emit()        

    def read(self, *args, **kwargs):
        data = File.read(self, *args, **kwargs) 
        if not data:
            self._atend = True
            self.completed.emit()
        else: self.__read.emit()
        return data

    def readLine(self, *args, **kwargs):
        data = File.readLine(self, *args, **kwargs)
        if not data: 
            self._atend = True
            self.completed.emit()
        else: self.__read.emit()
        return data

    def _emitReadyRead(self):
        self.readyRead.emit()

# -------------------------------------------------------------------------

if __name__=="__main__":
    import sys
    import traceback
    from boing.eventloop.EventLoop import EventLoop
    filepath = "filetest.dat"
    writer = File(filepath, IODevice.WriteOnly)
    print("Writing file:", writer.fileName())
    writer.write("This is a test.".encode())
    writer.close()
    del writer
    print()
    reader = File(filepath, IODevice.ReadOnly)
    print("Reading entire file:", reader.fileName())
    print(reader.readAll().decode())
    reader.close()
    del reader
    print()
    def dump():
        data = reader.read()
        if not data: EventLoop.stop()
        else: print(data.decode())
    reader = FileReader(filepath, IODevice.ReadOnly)
    reader.readyRead.connect(dump)
    print("Reading file along EventLoop:", reader.fileName())
    EventLoop.run()
    print()
    del reader
