# -*- coding: utf-8 -*-
#
# boing/nodes/logger.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import abc
import collections
import datetime
import math
import os
import sys
import weakref

from PyQt4 import QtCore, QtGui, uic

from boing.core import Offer, Request, Producer, Consumer
from boing.net import Decoder
from boing.utils import fileutils, quickdict, assertIsInstance

from boing.nodes.uiRecorder import Ui_RecWindow
#from boing.nodes.uiUrlDialog import Ui_UrlDialog


class ProductBuffer(QtCore.QObject):

    changed = QtCore.pyqtSignal()
    """Emitted anytime the product buffer changes."""

    productDrop = QtCore.pyqtSignal()
    """Emitted when the maximum number of products has been exceeded
    and some products must be dropped before the normal product's
    lifetime."""

    def __init__(self, sizelimit=10000, oversizecut=100, parent=None, **kwargs):
        super().__init__(parent)
        """Product buffer."""
        self._buffer = []
        """Number of products stored in buffer."""
        self._sum = 0
        """Maximum number of stored products."""
        self._sizelimit = None \
            if sizelimit is None or sizelimit==float("inf") \
            else assertIsInstance(sizelimit, int)
        """When stored products exceed 'sizelimit', instead of keeping
        'sizelimit' products, it keeps 'sizelimit'-'oversizecut'
        products, so that productDrop is not invoked anytime a new
        product is obtained."""
        self.oversizecut = assertIsInstance(oversizecut, int)
        # Connect argument slot
        for key, value in kwargs.items():
            if key=="changed": self.changed.connect(value)
            elif key=="productDrop": self.productDrop.connect(value)
            else: raise TypeError(
                "'%s' is an invalid keyword argument for this function"%key)

    def sizeLimit(self):
        return self._sizelimit

    def setSizeLimit(self, sizelimit):
        self._sizelimit = None \
            if sizelimit is None or sizelimit==float("inf") \
            else assertIsInstance(sizelimit, int)
        self._checkSizeLimit()

    def append(self, products):
        """Store products as a buffer item."""
        record = quickdict()
        record.timetag = datetime.datetime.now()
        record.products = products
        self._buffer.append(record)
        self._sum += len(products)
        if not self._checkSizeLimit(): self.changed.emit()

    # def pop(self):
    #     """Remove and return an element from the right side of the
    #     deque. If no elements are present, raises an IndexError."""
    #     return self._buffer.pop()

    # def popleft(self):
    #     """Remove and return an element from the left side of the
    #     deque. If no elements are present, raises an IndexError."""
    #     return self._buffer.popleft()

    def clear(self):
        """Clear the buffer."""
        del self._buffer[:]
        self._sum = 0
        self.changed.emit()

    def sum(self):
        """Return the total amount of stored products. It can be
        different from the buffer size, since each buffer item may
        stock several products."""
        return self._sum

    def index(self, timetag, start=0, end=None):
        """Index of the first element with timetag greater or equal
        than *timetag* or len(self) if there is no such item."""
        if end is None: end = len(self._buffer)
        for i in range(start, end):
            if self._buffer[i].timetag>=timetag: break
        else:
            i += 1
        return i

    def slice(self, starttime=None, endtime=None):
        """Return a slice of the buffer's elements. *starttime* and
        *endtime* must be datetime.datetime or None and they can be
        used to slice the buffer."""
        assertIsInstance(starttime, datetime.datetime, None)
        assertIsInstance(endtime, datetime.datetime, None)
        start = 0 if starttime is None else self.index(starttime)
        end = len(self._buffer) if endtime is None else self.index(endtime, start)
        return collections.deque(self._buffer[start:end])

    def islice(self, starttime=None, endtime=None):
        """Returns an iterator over the stored records {'timetag':
        ... , 'products': ...}.  *starttime* and *endtime* must be
        datetime.datetime or None and they can be used to slice the
        buffer."""
        assertIsInstance(starttime, datetime.datetime, None)
        assertIsInstance(endtime, datetime.datetime, None)
        for record in self._buffer:
            if starttime is not None and record.timetag<starttime: continue
            if endtime is not None and record.timetag>endtime: break
            yield record

    def _checkSizeLimit(self):
        if self._sizelimit is None: rvalue = False
        else:
            # Check maximum number of products
            if self._sum>self._sizelimit:
                count = 0
                for i, record in enumerate(self._buffer):
                    count += len(record.products)
                    if count>=self.oversizecut: break
                del self._buffer[:i+1]
                self._sum -= count
                self.productDrop.emit()
                rvalue = True
            else:
                rvalue = False
        return rvalue

    def __len__(self):
        """Return the number of elements of the buffer."""
        return len(self._buffer)

    def __getitem__(self, index):
        return self._buffer[index]

    def __delitem__(self, index):
        del self._buffer[index]

    def __iter__(self):
        return iter(self._buffer)

class TimedProductBuffer(ProductBuffer):
    """Elements have a fixed timelife and they are automatically
    removed when they are done.

    """
    def __init__(self, timelimit=30000, sizelimit=10000, eraserinterval=1000,
                 oversizecut=100, parent=None, **kwargs):
        super().__init__(sizelimit, oversizecut, parent, **kwargs)
        """Products timelife."""
        self._timelimit = None if timelimit is None or timelimit==float("inf") \
            else datetime.timedelta(milliseconds=timelimit)
        """Innovation timer timeout inverval."""
        self._eraserinterval = eraserinterval
        """Product timelife verifier."""
        self._eraser = QtCore.QTimer(timeout=self.erasingTime)
        if self._timelimit is not None: self._eraser.start(self._eraserinterval)

    def timeLimit(self):
        """Return the products' timelife."""
        return self._timelimit

    def setTimeLimit(self, msec):
        """Set the products' timelife."""
        self._timelimit = None if msec is None or msec==float("inf") \
            else datetime.timedelta(milliseconds=msec)
        self.stop() if self._timelimit is None else self.start()

    def eraserInterval(self):
        """Return the interval of the eraser timer, which checks the timelife
        of all the stored products."""
        return self._eraser.interval()

    def setEraserInterval(self, msec):
        """Set the interval of the eraser timer, which checks the timelife
        of all the stored products."""
        self._eraser.setInterval(msec)

    def isEraserActive(self):
        """Return whether the eraser is active."""
        return self._eraser.isActive()

    def setEraserActive(self, active):
        """Activate or deactivate the eraser timer."""
        if active and self._timelimit is not None:
            self._eraser.start(self._eraserinterval)
        else:
            self._eraser.stop()

    def erasingTime(self):
        """Check the timelife of all the stored products and drop the
        ones that are done."""
        if self._buffer:
            oldest = datetime.datetime.now()-self._timelimit
            count = 0
            for i, record in enumerate(self._buffer):
                if record.timetag>=oldest: break
                else:
                    count += len(record.products)
            else:
                i += 1
            if i>0:
                del self._buffer[:i]
                self._sum -= count
                self.changed.emit()

# -------------------------------------------------------------------

class BufferGraph(QtGui.QWidget):
    """The BufferGraph is a QWidget which displayes the content of a
    ProductBuffer.

    """
    def __init__(self, buffer, starttime=None, endtime=None,
                 fps=None, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self._buffer = buffer
        self._starttime = starttime if starttime is not None \
            else datetime.datetime.min
        self._endtime = endtime if endtime is not None \
            else datetime.datetime.max
        self._interval = None ; self._updateInterval()
        self._refresher = QtCore.QTimer(timeout=self._refresherTimeout)
        if fps is not None and fps!=0:
            self._toupdate = False
            self._buffer.changed.connect(self._bufferChanged)
            self._refresher.start(1000/fps)

    def startTime(self):
        """Return the lower time limit of the graph."""
        return self._starttime

    def setStartTime(self, starttime):
        """Set the lower time limit of the graph to *starttime*."""
        self._starttime = starttime if starttime is not None \
            else datetime.datetime.min
        self._updateInterval()
        self.update()

    def endTime(self):
        """Return the higher time limit of the graph."""
        return self._endtime

    def setEndTime(self, endtime):
        """Set the higher time limit of the graph to *endtime*."""
        self._endtime = endtime if endtime is not None \
            else datetime.datetime.max
        self._updateInterval()
        self.update()

    def setInterval(self, starttime, endtime):
        """Set both the start time and the end time."""
        self._starttime = starttime if starttime is not None \
            else datetime.datetime.min
        self._endtime = endtime if endtime is not None \
            else datetime.datetime.max
        self._updateInterval()
        self.update()

    def fps(self):
        """Return the graph's refresh frame rate."""
        return 0 if not self._refresher.isActive() \
            else 1/self._refresher.interval()

    def setFps(self, fps):
        """Set the graph's refresh frame rate."""
        if fps is None or fps==0:
            if self._refresher.isActive():
                self._buffer.changed.disconnect(self._bufferChanged)
                self._refresher.stop()
        else:
            self._toupdate = False
            if not self._refresher.isActive():
                self._buffer.changed.connect(self._bufferChanged)
            self._refresher.start(1000/fps)

    def _bufferChanged(self):
        self._toupdate = True

    def _refresherTimeout(self):
        if self._toupdate:
            self._toupdate = False
            self.update()

    def _updateInterval(self):
        old = self._interval
        self._interval = self._endtime-self._starttime
        if old!=self._interval: self._updateTimePrecision()

    def _updateTimePrecision(self):
        self._timeprecision = self._interval/self.width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._updateTimePrecision()

    def paintEvent(self, event):
        width, height = self.width(), self.height()
        painter = QtGui.QPainter(self)
        painter.setFont(QtGui.QFont( "courier", 9))
        painter.setPen(QtGui.QColor(200,200,200))
        # Draw grid
        for i in range(0, 100, 5):
            x = i*width/100
            y = i*height/100
            painter.drawLine(x, 0, x, height)
        painter.setPen(QtCore.Qt.black)
        painter.drawText(5,10, "# products: %d"%(self._buffer.sum()))
        # Draw products
        if self._buffer and self._interval!=datetime.timedelta():
            # Instead of printing all the records, jump directly to the record
            recorditer = self._buffer.islice(self._starttime, self._endtime)
            currtime = self._starttime
            while currtime<self._endtime:
                record = None
                while record is None:
                    candidate = next(recorditer, None)
                    if candidate is None: break
                    elif candidate.timetag>currtime:
                        record = candidate
                if record is None: break
                else:
                    dx = (self._endtime-record.timetag)/self._interval*width
                    painter.drawLine(width-dx, height, width-dx, height-30)
                    currtime += self._timeprecision


# -------------------------------------------------------------------

class Player(Producer):

    class Parser(metaclass=abc.ABCMeta):
        @abc.abstractmethod
        def parse(self): raise NotImplementedError()
        @abc.abstractmethod
        def reset(self): raise NotImplementedError()

    class Sender(metaclass=abc.ABCMeta):
        @abc.abstractmethod
        def send(self, player, obj): raise NotImplementedError()

    # FIXME: Sender should be rearchitectured.
    class PostSender(Sender):
        def send(self, player, obj): player.postProduct(obj)

    class ProductSender(Sender):
        def send(self, player, obj):
            for product in obj["products"]:
                # product["timetag"] = player._date if player._date is not None \
                # else datetime.datetime.now()
                player.postProduct(product)

    started = QtCore.pyqtSignal()
    stopped = QtCore.pyqtSignal()

    def __init__(self, parser, sender, speed=1.0, loop=False, interval=1000,
                 offer=Offer(Offer.UNDEFINED), parent=None):
        super().__init__(offer, parent=parent)
        self._parser = assertIsInstance(parser, Player.Parser)
        self._sender = assertIsInstance(sender, Player.Sender)
        self._loop = assertIsInstance(loop, bool)
        self._speed = float(speed) # speed factor
        self._interval = int(interval) # in ms
        self._queue = collections.deque()
        self._waittimer = QtCore.QTimer(timeout=self._parseSendOutAndWait)
        self._waittimer.setSingleShot(True)
        self._running = False
        self._date = None # Datetime when the next item should be sent.
        self.playcnt = 0

    def start(self):
        """Start the player."""
        if not self._running:
            self._running = True
            self.playcnt += 1
            self.started.emit()
            self._parseSendOutAndWait()

    def stop(self):
        """Stop the player."""
        if self._running:
            self._running = False
            self._stopPlaying()
            self.stopped.emit()

    def isRunning(self):
        """Return whether the player is currently reproducing a track."""
        return self._running

    def speed(self):
        """Return the playback speed factor."""
        return self._speed

    def setSpeed(self, speed):
        """Set the playback speed factor."""
        self._speed = float(speed)

    def interval(self):
        """Return the interval between two executions in ms."""
        return self._interval

    def setInterval(self, ms):
        """Set the interval between two executions to *ms*."""
        self._interval = float(ms)

    def parser(self):
        """Return the current parser."""
        return self._parser

    def sender(self):
        """Return the current sender."""
        return self._sender

    def setSender(self, sender):
        """Set a new sender."""
        self._sender = assertIsInstance(sender, Player.Sender)

    def _parseSendOutAndWait(self):
        # Parse for the first
        while not self._queue:
            proceed, *items = self.parser().parse()
            self._queue.extend(items)
            if not proceed: break
        if not self._queue: self.stop()
        else:
            # Send out the first
            first = self._queue.popleft()
            sendtime = datetime.datetime.now()
            self.sender().send(self, first)
            # Parse for the second
            while not self._queue:
                proceed, *items = self.parser().parse()
                self._queue.extend(items)
                if not proceed: break
            if not self._queue: self._finished()
            else:
                # Wait for the second
                if math.isinf(self._speed): msec = 0
                else:
                    firsttime = first.timetag if hasattr(first, "timetag") \
                        else first["timetag"] if "timetag" in first \
                        else sendtime
                    nexttime = self._queue[0].timetag \
                        if hasattr(self._queue[0], "timetag") \
                        else self._queue[0]["timetag"] \
                        if "timetag" in self._queue[0] \
                        else sendtime
                    delta = (nexttime-firsttime)/self._speed
                    if self._date is not None: delta -= sendtime-self._date
                    self._date = sendtime+delta
                    msec = 0 if delta.days<0 else delta.total_seconds()*1000
                self._waittimer.start(msec)

    def _stopPlaying(self):
        self._parser.reset()
        self._waittimer.stop()
        self._queue.clear()
        self._date = None

    def _finished(self):
        self._stopPlaying()
        self._waittimer.start(self._interval) if self._loop else self.stop()


class FilePlayer(Player):

    class FileParser(Player.Parser):
        def __init__(self, filepath, decoder=None):
            self._file = None if filepath is None \
                else fileutils.File(filepath, uncompress=True)
            self._decoder = assertIsInstance(decoder, Decoder, None)

        def file(self): return self._file
        def decoder(self): return self._decoder

        def setFile(self, filepath):
            if self._file is not None and self._file.isOpen():
                self.decoder().reset()
                self._file.close()
            self._file = None if filepath is None \
                else fileutils.File(filepath, uncompress=True)

        def setDecoder(self, decoder):
            self._decoder = assertIsInstance(decoder, Decoder)

        def parse(self):
            rvalue = False,
            if self.file() is not None and self.file().isOpen():
                data = self.file().read()
                if data:
                    if self.decoder() is not None:
                        rvalue = (True, ) + self.decoder().decode(data)
                    else:
                        rvalue = True, data
            return rvalue

        def reset(self):
            if self._file is not None and self._file.isOpen():
                self._file.seek(0)
            self.decoder().reset()

    def __init__(self, filepath, decoder=None, *args, **kwargs):
        super().__init__(self.FileParser(filepath, decoder), *args, **kwargs)

    def file(self): return self.parser().file()

    def setFile(self, filepath):
        return self.parser().setFile(filepath)

    def play(self, filepath):
        if self.isRunning(): self.stop()
        self.setFile(filepath)
        self.start()

class BufferPlayer(Player):

    class BufferParser(Player.Parser):
        def __init__(self, buffer):
            super().__init__()
            self._buffer = assertIsInstance(buffer, collections.Sequence)
            self._index = 0

        def buffer(self):
            return self._buffer

        def setBuffer(self, buffer):
            self._buffer = buffer
            self.reset()

        def parse(self):
            rvalue = False,
            if self._index<len(self.buffer()):
                rvalue = True, self.buffer()[self._index]
                self._index += 1
            return rvalue

        def reset(self): self._index = 0

    def __init__(self, parser=None, *args, **kwargs):
        if parser is None: parser = BufferPlayer.BufferParser(tuple())
        super().__init__(assertIsInstance(parser, BufferPlayer.BufferParser),
                         *args, **kwargs)

    def setBuffer(self, buffer):
        if self.isRunning(): raise Exception(
            "Cannot set buffer while player is running.")
        return self.parser().setBuffer(buffer)

    def play(self, buffer):
        if self.isRunning(): self.stop()
        self.setBuffer(buffer)
        self.start()

# -------------------------------------------------------------------

class Recorder(Consumer):

    class _InternalQObject(Consumer._InternalQObject):
        started = QtCore.pyqtSignal()
        stopped = QtCore.pyqtSignal()
        toggled = QtCore.pyqtSignal(bool)
        _writerToggled = QtCore.pyqtSignal(bool)

    @property
    def started(self):
        """Signal emitted when the recorder is started."""
        return self._internal.started

    @property
    def stopped(self):
        """Signal emitted when the recorder is stopped."""
        return self._internal.stopped

    @property
    def toggled(self):
        return self._internal.toggled

    @property
    def _writerToggled(self):
        return self._internal._writerToggled

    class Model:

        def __init__(self, buffer, active=False):
            self.buffer = buffer
            self.active = active
            self.writerActive = False

    def __init__(self, request=Request.ANY,
                 timelimit=30000, sizelimit=10000, timewarping=True,
                 oversizecut=100, fps=20, guiparent=None, parent=None):
        super().__init__(request, parent=parent)
        if fps<=0: raise ValueError(
            "fps must be a value greater than zero, not %s"%str(fps))
        self.fps = fps
        buffer= TimedProductBuffer(timelimit, sizelimit,
                                   oversizecut=oversizecut)
        # Deactivate the timed buffer eraser and use the refresher
        # timer instead.
        buffer.setEraserActive(False)
        self._model = Recorder.Model(buffer)
        """Determines whether the time when the buffer is stopped does not
        reduce the products timelife."""
        self.timewarping = assertIsInstance(timewarping, bool)
        """time when the recorder was stopped or None if the recorder
        is running."""
        self._stoptime = None
        self._refresher = QtCore.QTimer(timeout=self._refreshtime)
        # Writer
        self._writer = BufferPlayer(sender=Player.PostSender())
        self._writer.stopped.connect(self._writerStopped,
                                     QtCore.Qt.QueuedConnection)
        self._writer.setSpeed(float("inf"))
        self._writer.setSender(Player.PostSender())
        self._target = None
        # Setup GUI
        self._gui = Recorder.RecorderWindow(self._model, guiparent)
        self._gui.toggleActive.connect(self._toggleActive)
        self._gui.clearBuffer.connect(self.clearBuffer)
        self._gui.writeTo.connect(self.writeTo)
        self._gui.closed.connect(self.clear)
        self.toggled.connect(self._gui._recorderToggled)
        self._writerToggled.connect(self._gui._writerToggled)

    def gui(self): return self._gui

    def isActive(self):
        """Return whether the recorder is active."""
        return self._model.active

    def start(self):
        """Start product recording and product lifetime check."""
        self._setActive(True)

    def stop(self):
        """Stop product recording."""
        self._setActive(False)

    def clearBuffer(self):
        """Clear the recorder's buffer."""
        self._model.buffer.clear()

    def writeTo(self, uri):
        if not self._writer.isRunning():
            from boing import create
            self._target = create(uri)
            self._writer.addObserver(self._target)
            self._writer.play(self._model.buffer)
            self._model.writeActive = True
            self._writerToggled.emit(True)
        else:
            raise Exception("Recorder's writer is already running.")

    def _setActive(self, active):
        """Activate or deactivate the recorder."""
        if active!=self.isActive():
            self._model.active = active
            if super().request()!=Request.NONE: self.requestChanged.emit()
            if active:
                if self.timewarping and self._model.buffer:
                    # FIXME: this operation should be a ProductBuffer method
                    delta = datetime.datetime.now()-self._stoptime
                    for record in self._model.buffer:
                        record.timetag += delta
                self._stoptime = None
                self._refreshtime()
                self._refresher.start(1000/self.fps)
                self.started.emit()
            else:
                self._stoptime = datetime.datetime.now()
                self._refresher.stop()
                self.stopped.emit()
            self.toggled.emit(self.isActive())

    def _toggleActive(self):
        """Start the recorder if it is stopped or stop it, if it is running."""
        self._setActive(not self.isActive())

    def request(self):
        """Return the recorder's request if it is active."""
        return super().request() if self.isActive() else Request.NONE

    def _consume(self, products, source):
        """If active, it appends into the buffer the received products."""
        if self.isActive():
            self._model.buffer.append(products)

    def _refreshtime(self):
        self._model.buffer.erasingTime()
        now = datetime.datetime.now()
        timelimit = self._model.buffer.timeLimit()
        if timelimit is None:
            # Set only the end time
            self.gui().graph.setEndTime(now)
        else:
            # Set both starttime and endtime
            self.gui().graph.setInterval(now-timelimit, now)

    def _writerStopped(self):
        self._writer.clear()
        # Let the write operation end.
        QtCore.QTimer.singleShot(50, self._clearTarget)

    def _clearTarget(self):
        self._target = None
        self._model.writeActive = False
        self._writerToggled.emit(False)


    class RecorderWindow(QtGui.QMainWindow, Ui_RecWindow):
        """MainWindow of the recorder tool."""

        toggleActive = QtCore.pyqtSignal()
        """Signal emitted when the user requires to toggle the
        recorder status."""

        clearBuffer = QtCore.pyqtSignal()
        """Signal emitted when the user requires to clear the
        buffer."""

        writeTo = QtCore.pyqtSignal(str)
        """Signal emitted when the user requires to write the content
        of the buffer to a target destination."""

        closed = QtCore.pyqtSignal()
        """Signal emitted when the Widget is closed."""

        def __init__(self, model, parent=None):
            super().__init__(parent)
            self.setupUi(self)
            self.recordstop.triggered.connect(self.toggleActive)
            self.startstop.clicked.connect(self.toggleActive)
            self.clear.triggered.connect(self.clearBuffer)
            self.saveas.triggered.connect(self._selectFileDialog)
            self.quit.triggered.connect(QtGui.QApplication.instance().quit)
            # Graph widget
            self.graph = Recorder.RecorderGraph(model, fps=0)
            self.graph.toggleActive.connect(self.toggleActive)
            self.graph.clearBuffer.connect(self.clearBuffer)
            self.graph.saveAs.connect(self._selectFileDialog)
            self.framelayout.addWidget(self.graph)

        def _recorderToggled(self, active):
            self.startstop.setChecked(active)
            self.saveas.setEnabled(not active)
            self.graph._recorderToggled(active)

        def _writerToggled(self, active):
            self.startstop.setEnabled(not active)
            self.saveas.setEnabled(not active)

        def _selectFileDialog(self):
            """Execute a QFileDialog for selecting a target file."""
            dialog = QtGui.QFileDialog(self)
            dialog.setFileMode(QtGui.QFileDialog.AnyFile) # Existing files
            dialog.setViewMode(QtGui.QFileDialog.List)
            dialog.setAcceptMode(QtGui.QFileDialog.AcceptSave)
            if dialog.exec_():
                filepath, *useless = dialog.selectedFiles()
                sysprefix = "/" if sys.platform=="win32" else ""
                self.writeTo.emit("out.pickle.slip.file://%s%s"%(sysprefix,
                                                                 filepath))

        def closeEvent(self, event):
            self.closed.emit()
            super().closeEvent(event)

    class RecorderGraph(BufferGraph):
        """Widget showing the content of the buffer."""

        toggleActive = QtCore.pyqtSignal()
        """Signal emitted when the user requires to toggle the
        recorder status."""

        clearBuffer = QtCore.pyqtSignal()
        """Signal emitted when the user requires to clear the
        buffer."""

        saveAs = QtCore.pyqtSignal()
        """Signal emitted when the user requires to save the buffer."""

        def __init__(self, model, fps=None, parent=None):
            now = datetime.datetime.now()
            super().__init__(model.buffer, now, now, fps, parent)
            self._model = model
            self.setFocus(QtCore.Qt.OtherFocusReason)
            # Init context menu
            self.menu = QtGui.QMenu(self)
            self.menu.addAction("Record/Stop", self.toggleActive, "Space")
            self.menu.addSeparator()
            self.saveas = QtGui.QAction("Save as...", self.menu)
            self.saveas.triggered.connect(self.saveAs)
            self.saveas.setShortcut("Ctrl+S")
            self.menu.addAction(self.saveas)
            self.menu.addSeparator()
            self.menu.addAction("Clear buffer", self.clearBuffer, "Ctrl+C")

        def _recorderToggled(self, active):
            self.saveas.setEnabled(not active)
            self.update()

        def contextMenuEvent(self, event):
            """Display the context menu if the recorder is not writing to file."""
            if not self._model.writerActive: self.menu.exec_(event.globalPos())

        def paintEvent(self, event):
            super().paintEvent(event)
            # Draw rec point
            if self._model.active:
                painter = QtGui.QPainter(self)
                painter.setFont(QtGui.QFont( "courier", 9))
                painter.setPen(QtGui.QColor(100,100,100))
                painter.drawText(self.width()-25,10, "REC")
                painter.setPen(QtCore.Qt.red)
                painter.setBrush(QtCore.Qt.red)
                painter.drawEllipse(self.width()-34, 3, 6, 6)
