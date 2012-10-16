=================================================
 :mod:`boing.utils.fileutils` --- File utilities
=================================================

.. module:: boing.utils.fileutils
   :synopsis: File utilities

The module :mod:`boing.utils.fileutils` provides some useful classes
for having a standard interface over standard device files, Unix
non-standard files and tty devices.

It has also been created because it was necessary a more extensive
support to the Unix non-standard devices (i.e. named pipes and device
files) rather the one provided from the Qt framework.

Input/Output devices
====================

.. class:: IODevice(fd, parent=None)

   The :class:`IODevice` provides a standard interface for the
   generic file descriptors *fd*, which it could be a file, the
   stdin or the stdout.

   .. attribute:: bytesWritten

      Signal emitted when a write operation has been effectuated.

   .. attribute:: aboutToClose

     This signal is emitted when the device is about to close. Connect
     this signal if you have operations that need to be performed
     before the device closes (e.g., if you have data in a separate
     buffer that needs to be written to the device).

   .. method:: fd()

      Return the device's file descriptor.

   .. method:: isatty()

      Return ``True`` if the stream is interactive (i.e., connected to a
      terminal/tty device)

   .. method:: isOpen()

      Return whether the device is open.

   .. method:: isTextModeEnabled()

      Return whether the device provides unicode string rather
      than bytestream using the read methods.

   .. method:: bytesToWrite()

      Return the number of bytes that are waiting to be written.

   .. method:: flush()

      Flush the write buffers of the stream if applicable. This does
      nothing for read-only and non-blocking streams.

   .. method:: close()

      Flush and close this stream. This method has no effect if
      the file is already closed. Once the file is closed, any
      operation on the file (e.g. reading or writing) will raise a
      :exc:`ValueError`.

   .. method:: read(size=io.DEFAULT_BUFFER_SIZE)

      Read and return *size* bytes, or if n is not given or negative,
      until EOF or if the read call would block in non-blocking mode.

   .. method:: readline(limit=-1)

      Read and return one line from the stream.  If *limit* is
      specified, at most *limit* bytes will be read.

      The line terminator is always ``b'\n'`` for binary files; for
      text files, the *newlines* argument to :func:`open` can be used
      to select the line terminator(s) recognized.

   .. method:: readall()

      Read and return all the bytes from the stream until EOF, using
      multiple calls to the stream if necessary.

   .. method:: seek(offset, whence=io.SEEK_SET)

      Change the stream position to the given byte *offset*.  *offset*
      is interpreted relative to the position indicated by *whence*.
      Values for *whence* are:

      * :data:`SEEK_SET` or ``0`` -- start of the stream (the default);
        *offset* should be zero or positive
      * :data:`SEEK_CUR` or ``1`` -- current stream position; *offset* may
        be negative
      * :data:`SEEK_END` or ``2`` -- end of the stream; *offset* is usually
        negative

      Return the new absolute position.

   .. method:: write(data)

      Write the given bytes or bytearray object, b and return the
      number of bytes written. It also emit the signal
      :attr:`bytesWritten`.

   The :class:`IODevice` class also defines the following constants:

   .. attribute:: ReadOnly

   .. attribute:: WriteOnly

   .. attribute:: ReadWrite

   .. attribute:: Append


.. class:: CommunicationDevice(fd, parent=None)

   Specific class for devices for which the readyRead signal is
   usefull, like for example Unix not regular files and
   stdin. TcpSocket and UdpSocket do not inherit this class because
   they inherit specific Qt classes.

   .. attribute:: readyRead

      This signal is emitted once every time new data is available for
      reading from the device. It will only be emitted again once a
      new block of data has been appended to your device.

File support
============

.. class:: File(url, mode=IODevice.ReadOnly, uncompress=False, parent=None)

   :class:`File` instances represent a single file or directory.


.. class:: CommunicationFile(url, mode=IODevice.ReadOnly, parent=None)

   :class:`CommunicationFile` instances are used to access to
   Unix non-standard files. The argument *url* defines the path
   to the file to represent. *mode* can be set to:

   * :const:`IODevice.ReadOnly`
   * :const:`IODevice.WriteOnly`
   * :const:`IODevice.ReadWrite`
   * :const:`IODevice.Append`

.. class:: FileReader(url, , mode=IODevice.ReadOnly, uncompress=False, parent=None)

   The :class:`FileReader` can be used to read regular files along the
   event loop. When the method :meth:`start` is invoked, the
   :class:`FileReader` will trigger the :const:`readyRead` signal and
   it will repeat it every time the read method is invoked.

   .. attribute:: readyRead

      This signal is emitted once every time new data is available for
      reading from the device. It will only be emitted again once a
      new block of data has been appended to your device.

   .. attribute:: completed

      Signal emitted when the file has been completed.

   .. method:: start()

      Start reading the file.
