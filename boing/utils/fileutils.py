# -*- coding: utf-8 -*-
#
# boing/utils/fileutils.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import io
import os
import sys

from PyQt4 import QtCore

from boing.utils.url import URL

class IODevice(QtCore.QObject):
    """Class for wrapping a generic file descriptor, like a file,
    the stdin or the stdout."""

    # Open mode
    ReadOnly = 0x01
    WriteOnly = 0x02
    ReadWrite = 0x03
    Append = 0x04

    # Signals
    bytesWritten = QtCore.pyqtSignal(int)
    aboutToClose = QtCore.pyqtSignal()

    def __init__(self, fd, parent=None):
        QtCore.QObject.__init__(self, parent)
        self.__fd = fd
        self.__isatty = fd.isatty() if hasattr(fd, "isatty") else False
        self.__textModeEnabled = isinstance(self.__fd, io.TextIOBase)

    def __del__(self):
        try:
            if not self.__isatty: self.__fd.close()
        except Exception:
            pass

    def fd(self):
        return self.__fd

    def isatty(self):
        return self.__isatty

    def isOpen(self):
        return not self.__fd.closed

    def isTextModeEnabled(self):
        return self.__textModeEnabled

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

    readyRead = QtCore.pyqtSignal()

    def __init__(self, fd, parent=None):
        IODevice.__init__(self, fd, parent)
        self.__notifier = QtCore.QSocketNotifier(fd if type(fd)==int else fd.fileno(),
                                                 QtCore.QSocketNotifier.Read,
                                                 activated=self.readyRead)

    def __del__(self):
        super().__del__()
        try:
            self.__notifier.setEnabled(False)
        except Exception:
            pass
# -------------------------------------------------------------------

def openFile(filepath, mode=IODevice.ReadOnly, uncompress=False):
    """Open a file and return its file descriptor. If 'uncompress' is
    True and 'filepath' points to a compressed archive, the
    correspondent python module will be used to obtain the file
    descriptor."""
    if not isinstance(uncompress, bool): raise TypeError(
        "uncompress must be boolean, not '%s'"%uncompress.__class__.__name__)
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
        path = str(url.path)
        # Consider c:/tmp instead of /c:/tmp
        if sys.platform=="win32" and url.path.isAbsolute():
            path = path[1:]
        self._fileinfo = QtCore.QFileInfo(path)

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
    event loop. When the 'start' method is invoked, the FileReader will
    trigger the readyRead signal and it will repeat it every time the
    read method is invoked."""

    readyRead = QtCore.pyqtSignal()
    completed = QtCore.pyqtSignal()
    __read = QtCore.pyqtSignal()

    def __init__(self, url, mode=IODevice.ReadOnly,
                 uncompress=False, parent=None):
        File.__init__(self, url, mode, uncompress, parent)
        self._atend = False
        self.__read.connect(self.readyRead, QtCore.Qt.QueuedConnection)

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

# -------------------------------------------------------------------------

if __name__=="__main__":
    import sys
    import traceback
    app = QtCore.QCoreApplication(sys.argv)
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
    print()
    def dump():
        data = reader.read()
        if not data: app.quit()
        else: print(data.decode())
    reader = FileReader(filepath, IODevice.ReadOnly)
    reader.readyRead.connect(dump)
    print("Reading file along event loop:", reader.fileName())
    reader.start()
    sys.exit(app.exec_())
