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
import weakref

from PyQt4 import QtCore, QtGui, uic

from boing.core import Offer, Request, Producer, Consumer
from boing.net import Decoder
from boing.utils import fileutils, quickdict, assertIsInstance

# Compile all .ui files in this directory
uic.compileUiDir(os.path.dirname(__file__))
from boing.nodes.uiRecorder import Ui_recorder
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
        self._interval = self._endtime-self._starttime
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
        self._interval = self._endtime-self._starttime
        self.update()

    def endTime(self):
        """Return the higher time limit of the graph."""
        return self._endtime

    def setEndTime(self, endtime):
        """Set the higher time limit of the graph to *endtime*."""
        self._endtime = endtime if endtime is not None \
            else datetime.datetime.max
        self._interval = self._endtime-self._starttime
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
            for record in self._buffer.islice(self._starttime, self._endtime):
                dx = (self._endtime-record.timetag)/self._interval*width
                painter.drawLine(width-dx, height, width-dx, height-30)

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

    @property
    def started(self):
        return self._internal.started

    @property
    def stopped(self):
        return self._internal.stopped

    def __init__(self, request=Request.ANY,
                 timelimit=30000, sizelimit=10000, timewarping=True,
                 oversizecut=100, fps=60, guiparent=None, parent=None):
        super().__init__(request, parent=parent)
        if fps<=0: raise ValueError(
            "fps must be a value greater than zero, not %s"%str(fps))
        self.fps = fps
        self._active = False
        self._buffer = TimedProductBuffer(timelimit, sizelimit,
                                          oversizecut=oversizecut)
        # Deactivate the timed buffer eraser and use the refresher
        # timer instead.
        self._buffer.setEraserActive(False)
        """Determines whether the time when the buffer is stopped does not
        reduce the products timelife."""
        self.timewarping = assertIsInstance(timewarping, bool)
        """time when the recorder was stopped or None if the recorder
        is running."""
        self._stoptime = None
        self._refresher = QtCore.QTimer(timeout=self._refreshtime)
        self.gui = Recorder._Ui(self, guiparent)
        # Writer size
        self._writer = BufferPlayer(sender=Player.PostSender())
        self._writer.started.connect(self.gui.writerStarted)
        self._writer.stopped.connect(self._writerStopped)
        self._writerwaiter = QtCore.QTimer(timeout=self._checkWriter)

    def isActive(self):
        """Return whether the recorder is active."""
        return self._active

    def setActive(self, active):
        """Activate or deactivate the recorder."""
        self.start() if active else self.stop()

    def start(self):
        """Start product recording and product lifetime check."""
        if not self._active:
            self._active = True
            if super().request()!=Request.NONE: self.requestChanged.emit()
            if self.timewarping and self._buffer:
                # FIXME: this operation should be a ProductBuffer method
                delta = datetime.datetime.now()-self._stoptime
                for record in self._buffer:
                    record.timetag += delta
            self._stoptime = None
            self._refresher.start(1000/self.fps)
            self.gui.recorderStarted()
            self.started.emit()

    def stop(self):
        """Stop product recording, so that it will not store any other product
        and it will not loose any stored product."""
        if self._active:
            self._active = False
            if super().request()!=Request.NONE: self.requestChanged.emit()
            self._stoptime = datetime.datetime.now()
            self._refresher.stop()
            self.gui.recorderStopped()
            self.stopped.emit()

    def request(self):
        """Return the recorder's request."""
        return super().request() if self.isActive() else Request.NONE

    def _consume(self, products, source):
        if self._active: self._buffer.append(products)

    def writeTo(self, uri):
        if not self._writer.isRunning():
            from boing import create
            self._writer.addObserver(create(uri, mode="out"), child=True)
            self._writer.setSpeed(float("inf"))
            self._writer.setSender(Player.PostSender())
            self._writer.play(self._buffer)
        else:
            raise Exception("Recorder's writer is already running.")

    def playTo(self, uri):
        if not self._writer.isRunning():
            from boing import create
            self._writer.addObserver(create(uri, mode="out"), child=True)
            self._writer.setSpeed(1)
            self._writer.setSender(Player.ProductSender())
            self._writer.play(self._buffer)
        else:
            raise Exception("Recorder's writer is already running.")

    def _refreshtime(self):
        self._buffer.erasingTime()
        now = datetime.datetime.now()
        timelimit = self._buffer.timeLimit()
        if timelimit is not None: self.gui.graph.setStartTime(now-timelimit)
        self.gui.graph.setEndTime(now)

    def _writerStopped(self):
        self._writerwaiter.start(20)

    def _checkWriter(self):
        # FIXME: This actually is not enough to avoid
        # SegmentationFault. The fact of waiting 20ms actually helps.
        if not self._writer.hasPendingProducts():
            self._writerwaiter.stop()
            self._writer.clear()
            self.gui.writerStopped()

    class _Ui(QtGui.QWidget, Ui_recorder):

        class RecorderGraph(BufferGraph):

            def __init__(self, buffer, starttime=None, endtime=None,
                         fps=None, parent=None):
                super().__init__(buffer, starttime, endtime, fps, parent)
                self._recording = False

            def recorderStarted(self):
                self._recording = True
                self.update()

            def recorderStopped(self):
                self._recording = False
                self.update()

            def paintEvent(self, event):
                super().paintEvent(event)
                # Draw rec point
                if self._recording:
                    painter = QtGui.QPainter(self)
                    painter.setFont(QtGui.QFont( "courier", 9))
                    painter.setPen(QtGui.QColor(100,100,100))
                    painter.drawText(self.width()-25,10, "REC")
                    painter.setPen(QtCore.Qt.red)
                    painter.setBrush(QtCore.Qt.red)
                    painter.drawEllipse(self.width()-34, 3, 6, 6)

        def __init__(self, recorder, parent=None):
            super().__init__(parent)
            self.writeslot = recorder.writeTo
            self.playslot = recorder.playTo
            now = datetime.datetime.now()
            # Setup ui
            self.setupUi(self)
            self.graph = Recorder._Ui.RecorderGraph(recorder._buffer,
                                                    now, now, fps=0)
            self.graph.setFocus(QtCore.Qt.OtherFocusReason)
            self.graph.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            self.framelayout.addWidget(self.graph)
            self.startstop.toggled.connect(recorder.setActive)
            QtGui.QShortcut('Ctrl+Q', self,
                            activated=QtGui.QApplication.instance().quit)
            # Init context menu
            self.contextmenu = QtGui.QMenu(self)
            self.contextmenu.addAction("Start", recorder.start)
            self.contextmenu.addAction("Stop", recorder.stop)
            # self.contextmenu.addSeparator()
            # self.contextmenu.addAction("Play to dump:",
            #                            lambda: self.playslot("dump:"))
            self.contextmenu.addSeparator()
            self.contextmenu.addAction(
                "Write to file...", self._selectFileDialog)
            self.contextmenu.addSeparator()
            self.contextmenu.addAction("Clear buffer", recorder._buffer.clear)
            self.graph.customContextMenuRequested.connect(self._contextMenuRequested)
            # self.menu.addAction("To URL...", self._showUrlDialog)
            # self.urldialog = GestureBuffer.UrlDialog()
            # Add default actions
            # self.addUrlAction("viz:")
            # self.addUrlAction("dump:")
            # self.addUrlAction(os.path.join(os.path.expanduser("~"), "log.osc"))
            # self.addUrlAction("buffer:")

        def _contextMenuRequested(self, pos):
            self.contextmenu.exec_(self.graph.mapToGlobal(pos))

        def recorderStarted(self):
            self.startstop.setChecked(True)
            self.graph.recorderStarted()
            for action in self.contextmenu.actions():
                if action.text()=="Stop":
                    action.setEnabled(True)
                elif not action.isSeparator():
                    action.setEnabled(False)

        def recorderStopped(self):
            self.startstop.setChecked(False)
            self.graph.recorderStopped()
            for action in self.contextmenu.actions():
                if action.text()=="Stop":
                    action.setEnabled(False)
                elif not action.isSeparator():
                    action.setEnabled(True)

        def writerStarted(self):
            self.startstop.setEnabled(False)
            self.graph.setContextMenuPolicy(QtCore.Qt.NoContextMenu)

        def writerStopped(self):
            self.startstop.setEnabled(True)
            self.graph.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        def _selectFileDialog(self):
            """Execute a QFileDialog for selecting a target file."""
            dialog = QtGui.QFileDialog(self)
            # Select that only existing files can be opened
            dialog.setFileMode(QtGui.QFileDialog.AnyFile)
            dialog.setViewMode(QtGui.QFileDialog.List) # or Detail
            dialog.setAcceptMode(QtGui.QFileDialog.AcceptSave)
            if dialog.exec_():
                filepath, *useless = dialog.selectedFiles()
                self.writeslot("json.slip.file://%s"%filepath)

            '''DelayedReactive.__init__(self)
            QtGui.QWidget.__init__(self, parent)
            self.setFocusPolicy(QtCore.Qt.StrongFocus)
            self.buffer = buffer_
            self.subscribeTo(self.buffer)
            # Init context menu
            self.actionurls = set()
            self.menu = QtGui.QMenu(self)
            self.separator = QtGui.QAction(self.menu)
            self.separator.setSeparator(True)
            self.menu.addAction(self.separator)
            action = QtGui.QAction("To URL...", self.menu)
            action.triggered.connect(self._showUrlDialog)
            self.menu.addAction(action)
            action = QtGui.QAction('Clear', self.menu)
            action.triggered.connect(self.buffer.clear)
            self.menu.addAction(action)
            self.urldialog = GestureBuffer.UrlDialog()
            self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self._showMenu)
            # Add default actions
            self.addUrlAction("viz:")
            self.addUrlAction("dump:")
            self.addUrlAction(os.path.join(os.path.expanduser("~"), "log.osc"))
            self.addUrlAction("buffer:")
            self.refreshtimer = QtCore.QTimer()
            self.refreshtimer.timeout.connect(self.update)
            self.refreshtimer.start(self.buffer.innovationInterval())

        def addUrlAction(self, url):
            action = QtGui.QAction(url, self.menu)
            action.triggered.connect(self._urlAction)
            self.menu.insertAction(self.separator, action)
            self.actionurls.add(url)

        def _urlAction(self):
            sender = self.sender()
            if sender is not None: self.buffer.forwardTo(sender.text())

        def _showUrlDialog(self):
            self.urldialog.url.setText("")
            self.urldialog.url.setFocus(QtCore.Qt.OtherFocusReason)
            if self.urldialog.exec_():
                self.buffer.forwardTo(self.urldialog.url.text())'''
