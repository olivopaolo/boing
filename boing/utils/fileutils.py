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

"""The module :mod:`boing.utils.fileutils` provides some useful
classes for having a standard interface over standard device files,
Unix non-standard files and tty devices.

It has also been created because it was necessary a more extensive
support to the Unix non-standard devices (i.e. named pipes and device
files) rather the one provided from the Qt framework.

"""

class IODevice(QtCore.QObject):

    # Open mode
    ReadOnly = 0x01
    WriteOnly = 0x02
    ReadWrite = 0x03
    Append = 0x04

    # Signals
    bytesWritten = QtCore.pyqtSignal(int)
    """Signal emitted when a write operation has been effectuated."""

    aboutToClose = QtCore.pyqtSignal()
    """This signal is emitted when the device is about to
    close. Connect this signal if you have operations that need to be
    performed before the device closes (e.g., if you have data in a
    separate buffer that needs to be written to the device)."""

    def __init__(self, fd, parent=None):
        """The :class:`IODevice` provides a standard interface for the
        generic file descriptors *fd*, which it could be a file, the
        stdin or the stdout.

        """
        QtCore.QObject.__init__(self, parent)
        self.__fd = fd
        self.__isatty = fd.isatty() if hasattr(fd, "isatty") else False
        self.__textModeEnabled = isinstance(self.__fd, io.TextIOBase)

    def __del__(self):
        try:
            if not self.__isatty: self.__fd.close()
        except Exception: pass

    def fd(self):
        """Return the device's file descriptor."""
        return self.__fd

    def isatty(self):
        """Return ``True`` if the stream is interactive (i.e., connected
        to a terminal/tty device)."""
        return self.__isatty

    def isOpen(self):
        """Return whether the device is open."""
        return not self.__fd.closed

    def isTextModeEnabled(self):
        """Return whether the device provides unicode string rather
        than bytestream using the read methods."""
        return self.__textModeEnabled

    def bytesToWrite(self):
        """Return the number of bytes that are waiting to be written."""
        return 0

    def flush(self):
        """Flush the write buffers of the stream if applicable. This
        does nothing for read-only and non-blocking streams."""
        if hasattr(self.__fd, "flush"): self.__fd.flush()

    def close(self):
        """Flush and close this stream. This method has no effect if
        the file is already closed. Once the file is closed, any
        operation on the file (e.g. reading or writing) will raise a
        :exc:`ValueError`."""
        self.aboutToClose.emit()
        self.__fd.close()

    def read(self, size=io.DEFAULT_BUFFER_SIZE):
        """Read and return *size* bytes, or if n is not given or
        negative, until EOF or if the read call would block in
        non-blocking mode."""
        data = self.__fd.read(size) if not self.__isatty else self.__fd.readline(size)
        return data

    def readLine(self, limit=-1):
        """Read and return one line from the stream.  If *limit* is
        specified, at most *limit* bytes will be read.

        The line terminator is always ``b'\n'`` for binary files; for
        text files, the *newlines* argument to :func:`open` can be
        used to select the line terminator(s) recognized."""
        return self.__fd.readline(limit)

    def readAll(self):
        """Read and return all the bytes from the stream until EOF,
        using multiple calls to the stream if necessary."""
        return self.__fd.readall()

    def write(self, data):
        """Write the given bytes or bytearray object, b and return the
        number of bytes written. It also emit the signal
        :attr:`bytesWritten`."""
        n = self.__fd.write(data)
        if n: self.bytesWritten.emit(n)
        return n

    def seek(self, offset, whence=io.SEEK_SET):
        """Change the stream position to the given byte *offset*.  *offset* is
        interpreted relative to the position indicated by *whence*.  Values for
        *whence* are:

        * :data:`SEEK_SET` or ``0`` -- start of the stream (the
          default); offset* should be zero or positive

        * :data:`SEEK_CUR` or ``1`` -- current stream position; *offset* may
          be negative

        * :data:`SEEK_END` or ``2`` -- end of the stream; *offset* is usually
           negative

        Return the new absolute position."""
        return self.__fd.seek(offset, whence)


class CommunicationDevice(IODevice):

    readyRead = QtCore.pyqtSignal()
    """This signal is emitted once every time new data is available
    for reading from the device. It will only be emitted again once a
    new block of data has been appended to your device."""

    def __init__(self, fd, parent=None):
        """Specific class for devices for which the readyRead signal
        is usefull, like for example Unix not regular files and
        stdin. TcpSocket and UdpSocket do not inherit this class
        because they inherit specific Qt classes.

        """
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

def _openFile(filepath, mode=IODevice.ReadOnly, uncompress=False):
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


class BaseFile:

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

    def __init__(self, url, mode=IODevice.ReadOnly, uncompress=False,
                 parent=None):
        """:class:`File` instances represent a single file or directory."""
        BaseFile.__init__(self, url)
        IODevice.__init__(self,
                          _openFile(self.absoluteFilePath(),
                                    mode, uncompress),
                          parent)


class CommunicationFile(BaseFile, CommunicationDevice):

    def __init__(self, url, mode=IODevice.ReadOnly, parent=None):
        """:class:`CommunicationFile` instances are used to access to
        Unix non-standard files. The argument *url* defines the path
        to the file to represent. *mode* can be set to:

        * IODevice.ReadOnly
        * IODevice.WriteOnly
        * IODevice.ReadWrite
        * IODevice.Apppend
        """
        BaseFile.__init__(self, url)
        CommunicationDevice.__init__(self,
                                     _openFile(self.absoluteFilePath(),
                                               mode),
                                     parent)

# -------------------------------------------------------------------------

class FileReader(File):

    readyRead = QtCore.pyqtSignal()
    """This signal is emitted once every time new data is available
    for reading from the device. It will only be emitted again once a
    new block of data has been appended to your device."""

    completed = QtCore.pyqtSignal()
    """Signal emitted when the file has been completed."""
    __read = QtCore.pyqtSignal()

    def __init__(self, url, mode=IODevice.ReadOnly,
                 uncompress=False, parent=None):
        """The :class:`FileReader` can be used to read regular files
        along the event loop. When the method :meth:`start` is
        invoked, the :class:`FileReader` will trigger the
        :const:`readyRead` signal and it will repeat it every time the
        read method is invoked.

        """
        File.__init__(self, url, mode, uncompress, parent)
        self._atend = False
        self.__read.connect(self.readyRead, QtCore.Qt.QueuedConnection)

    def atEnd(self):
        return self._atend

    def start(self):
        """Start reading the file."""
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
