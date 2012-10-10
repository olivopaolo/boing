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

from PyQt4 import QtCore, QtGui

from boing.core import Offer, Request, Producer, Consumer
from boing.net import Decoder
from boing.utils import fileutils, quickdict, assertIsInstance

from boing.nodes.uiRecorder import Ui_RecWindow
from boing.nodes.uiPlayToURIDialog import Ui_PlayToURIDialog

from boing import config as _config

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
        if self._buffer and self._timelimit is not None:
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

class BufferView(QtGui.QWidget):
    """The BufferView is a QWidget which displayes the content of a
    ProductBuffer.

    """

    selectionChanged = QtCore.pyqtSignal()
    """Signal emitted when the buffer selection has changed."""

    viewChanged = QtCore.pyqtSignal()
    """Signal emitted when the view window has changed."""

    def __init__(self, buffer, begin=None, end=None, fps=None,
                 graph=None, parent=None):
        super().__init__(parent)
        # Setup GUI
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setSpacing(4)
        self.graph = BufferView.Graph(weakref.proxy(self)) \
            if graph is None else graph(weakref.proxy(self))
        self.layout().addWidget(self.graph)
        self.scroll = QtGui.QScrollBar(QtCore.Qt.Horizontal,
                                       valueChanged=self._scrollTo)
        self.scroll.setPageStep(50)
        QtGui.QShortcut("Left", self.scroll, self._scrollLeft)
        QtGui.QShortcut("Right", self.scroll, self._scrollRight)
        QtGui.QShortcut("Alt+Left", self.scroll, self._scrollPageLeft)
        QtGui.QShortcut("Alt+Right", self.scroll, self._scrollPageRight)
        QtGui.QShortcut(QtCore.Qt.Key_PageUp, self.scroll, self._scrollPageLeft)
        QtGui.QShortcut(QtCore.Qt.Key_PageDown, self.scroll, self._scrollPageRight)
        QtGui.QShortcut("Ctrl+Up", self.scroll, self.zoomIn)
        QtGui.QShortcut("Ctrl+Down", self.scroll, self.zoomOut)
        QtGui.QShortcut("Home", self.scroll, self._scrollBegin)
        QtGui.QShortcut("End", self.scroll, self._scrollEnd)
        self.layout().addWidget(self.scroll)
        # Model
        self._buffer = buffer
        self._begin = assertIsInstance(begin, datetime.datetime) \
            if begin is not None else datetime.datetime.min
        self._end = assertIsInstance(end, datetime.datetime) \
            if end is not None else datetime.datetime.max
        # Zooming
        self._zoom = None
        self._zoomdelta = datetime.timedelta()
        self._viewbegin = self.begin()
        self._viewend = self.end()
        self._viewinterval = None
        self.zoomOriginal()
        # Selection
        self._selbegin = self._selend = self.begin()
        # Refresh timer
        self._refresher = QtCore.QTimer(timeout=self._refresherTimeout)
        if fps is not None and fps!=0:
            self._toupdate = False
            self._buffer.changed.connect(self._bufferChanged)
            self._refresher.start(1000/fps)

    def begin(self):
        """Return the lower time limit of the graph."""
        return self._begin

    def setBegin(self, begin):
        """Set the lower time limit of the graph to *begin*."""
        self._begin = assertIsInstance(begin, datetime.datetime) \
            if begin is not None else datetime.datetime.min
        self._updateView()

    def end(self):
        """Return the higher time limit of the graph."""
        return self._end

    def setEnd(self, end):
        """Set the higher time limit of the graph to *end*."""
        self._end = assertIsInstance(end, datetime.datetime) \
            if end is not None else datetime.datetime.max
        self._updateView()

    def setInterval(self, begin, end):
        """Set both the start time and the end time."""
        self._begin = assertIsInstance(begin, datetime.datetime) \
            if begin is not None else datetime.datetime.min
        self._end = assertIsInstance(end, datetime.datetime) \
            if end is not None else datetime.datetime.max
        self._updateView()

    def zoom(self):
        return self._zoom

    @QtCore.pyqtSlot()
    def zoomIn(self):
        self._changeZoom(self.zoom())

    @QtCore.pyqtSlot()
    def zoomOut(self):
        self._changeZoom(-self.zoom()*0.5)

    @QtCore.pyqtSlot()
    def zoomOriginal(self):
        self._zoom = 1.0
        self._zoomdelta = datetime.timedelta()
        self.scroll.setMaximum(0)
        self._updateView()

    def _changeZoom(self, delta, where=0.5):
        center = (self._viewend-self._viewbegin)*where+self._zoomdelta
        self._zoom += delta
        if self._zoom < 1.0:
            self._zoom = 1.0
            self._zoomdelta = datetime.timedelta()
        else:
            interval = (self.end()-self.begin())/self.zoom()
            self._zoomdelta = center-interval*where
        self._updateView()
        # When zooming out verify that zoomdelta do not let show
        # outside the buffer.
        max = self.end()-self.begin()-self._viewinterval
        if self._zoomdelta>max:
            self._zoomdelta = max
            self._updateView()
        # Configure scrollbar
        tics = 0 if self.zoom()==1.0 \
            else math.log(max.total_seconds())*100*self.zoom()
        pos = 0 if max==datetime.timedelta() else \
            int(self._zoomdelta/max*tics)
        self.scroll.setMaximum(tics)
        self.scroll.setValue(pos)

    @QtCore.pyqtSlot(int)
    def _scrollTo(self, value):
        if self.scroll.maximum()!=0:
            self._zoomdelta = \
                value/self.scroll.maximum() \
                * (self.end()-self.begin()-self._viewinterval)
            if self._zoomdelta.total_seconds()<0:
                self._zoomdelta = datetime.timedelta()
            else:
                max = self.end()-self.begin()-self._viewinterval
                if self._zoomdelta>max: self._zoomdelta = max
            self._updateView()

    @QtCore.pyqtSlot(float)
    def _scrollLeft(self, value=10.0):
        self.scroll.setValue(self.scroll.value()-value)

    @QtCore.pyqtSlot(float)
    def _scrollRight(self, value=10.0):
        self.scroll.setValue(self.scroll.value()+value)

    @QtCore.pyqtSlot()
    def _scrollPageLeft(self):
        self.scroll.setValue(self.scroll.value()-self.scroll.pageStep())

    @QtCore.pyqtSlot()
    def _scrollPageRight(self):
        self.scroll.setValue(self.scroll.value()+self.scroll.pageStep())

    @QtCore.pyqtSlot()
    def _scrollBegin(self):
        self.scroll.setValue(self.scroll.minimum())

    @QtCore.pyqtSlot()
    def _scrollEnd(self):
        self.scroll.setValue(self.scroll.maximum())

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

    def selection(self):
        """Return a tuple (begin, end) representing the selection."""
        return (self._selbegin, self._selend) \
            if self._selbegin<=self._selend \
            else (self._selend, self._selbegin)

    def hasSelectedItems(self):
        """Return whether the current selection contains any buffered
        items."""
        rvalue = False
        for record in self._buffer.islice(*self.selection()):
            rvalue = True ; break
        return rvalue

    def selectAll(self):
        """Select the entire interval."""
        self._selbegin = self._viewbegin
        self._selend = self._viewend
        self.selectionChanged.emit()
        self.update()

    def clearSelection(self):
        """Clear the selection."""
        self._selbegin = self._selend = self.begin()
        self.selectionChanged.emit()
        self.update()

    def _updateView(self):
        """Determine the view variables."""
        old = self._viewinterval
        if self.zoom()==1:
            self._viewbegin = self.begin()
            self._viewend = self.end()
            self._viewinterval = self._viewend-self._viewbegin
        else:
            self._viewinterval = (self.end()-self.begin())/self.zoom()
            self._viewbegin = self.begin()+self._zoomdelta
            self._viewend = self._viewbegin+self._viewinterval
        # Determine graph reference scale
        interval = self._viewinterval.total_seconds()
        exp = int(math.log10(interval))
        delta = self.end()-self._viewend
        seconds = delta.total_seconds()
        seconds = int(seconds/10**exp)*10**(exp)
        self._graphreftime = \
            self.end()-datetime.timedelta(seconds=seconds)
        self._graphlineinterval = datetime.timedelta(seconds=10**(exp-1))
        if old!=self._viewinterval: self._updateTimePrecision()
        self.viewChanged.emit()
        self.update()

    def _updateTimePrecision(self):
        self._timeprecision = self._viewinterval.total_seconds()/(self.graph.width()-2)

    @QtCore.pyqtSlot()
    def _bufferChanged(self):
        """Notes that the buffer has changed so an update is
        necessary."""
        self._toupdate = True

    @QtCore.pyqtSlot()
    def _refresherTimeout(self):
        """Refresher timeout slot."""
        if self._toupdate: self._toupdate = False ; self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._updateTimePrecision()


    class Graph(QtGui.QFrame):

        def __init__(self, bufferview, parent=None):
            super().__init__(parent)
            self._bufferview = bufferview
            self.setFrameShape(QtGui.QFrame.StyledPanel)
            self.setFrameShadow(QtGui.QFrame.Raised)

        def mousePressEvent(self, event):
            if event.button()==QtCore.Qt.LeftButton:
                begin = self._bufferview._viewend-datetime.timedelta(seconds=(self.width()-event.x())*self._bufferview._timeprecision)
                self._bufferview._selbegin = self._bufferview._selend = begin
                self._bufferview.selectionChanged.emit()
                self.update()
                event.accept()
            else:
                super().mousePressEvent(event)

        def mouseMoveEvent(self, event):
            self._bufferview._selend = self._bufferview._viewend-datetime.timedelta(seconds=(self.width()-event.x())*self._bufferview._timeprecision)
            self._bufferview.selectionChanged.emit()
            self.update()
            event.accept()

        def wheelEvent(self, event):
            event.accept()
            if event.modifiers()==QtCore.Qt.ControlModifier \
                    and event.orientation()==QtCore.Qt.Vertical:
                # Zoom
                self._bufferview._changeZoom(
                    event.delta()*0.001*self._bufferview.zoom(),
                    event.x()/self.width())
            else:
                if self._bufferview.zoom()!=1.0:
                    # Scroll
                    factor = 1 if event.modifiers()==QtCore.Qt.AltModifier \
                        else 0.1
                    self._bufferview._scrollLeft(event.delta()*factor) \
                        if event.delta()>0 \
                        else self._bufferview._scrollRight(-event.delta()*factor)

        def paintEvent(self, event):
            super().paintEvent(event)
            width, height = self.width()-2, self.height()-20
            painter = QtGui.QPainter(self)
            painter.setFont(QtGui.QFont( "courier", 9))
            lightpen = QtGui.QPen(QtGui.QColor(200,200,200))
            darkpen = QtGui.QPen(QtGui.QColor(150,150,150))
            i = 0
            temp = self._bufferview._viewend-self._bufferview._graphreftime
            refx = width \
                - temp.total_seconds()/self._bufferview._timeprecision
            dx = self._bufferview._graphlineinterval.total_seconds() \
                / self._bufferview._timeprecision
            reft = self._bufferview.end()-self._bufferview._graphreftime
            while refx>0:
                i += 1
                refx -= dx
                reft += self._bufferview._graphlineinterval
                if refx<width and refx>0:
                    if i%10==0:
                        painter.setPen(darkpen)
                        painter.drawText(
                            refx-self.width()*0.5, height, self.width(), 12, QtCore.Qt.AlignHCenter,
                            str(reft))
                    else:
                        painter.setPen(lightpen)
                    painter.drawLine(refx, 2, refx, height)
            painter.setPen(QtCore.Qt.black)
            painter.drawText(5,10, "# products: %d"%(self._bufferview._buffer.sum()))
            # Draw products
            if self._bufferview._buffer and self._bufferview._viewinterval!=datetime.timedelta():
                # Instead of printing all the records, jump directly to the record
                recorditer = self._bufferview._buffer.islice(self._bufferview._viewbegin, self._bufferview._viewend)
                currtime = self._bufferview._viewbegin
                while currtime<self._bufferview._viewend:
                    record = None
                    while record is None:
                        candidate = next(recorditer, None)
                        if candidate is None: break
                        elif candidate.timetag>currtime:
                            record = candidate
                    if record is None: break
                    else:
                        dt = self._bufferview._viewend-record.timetag
                        dx = dt.total_seconds()/self._bufferview._timeprecision
                        painter.drawLine(width-dx+1, height, width-dx+1, height-30)
                        currtime += datetime.timedelta(seconds=self._bufferview._timeprecision)
            # Draw selection
            if self._bufferview._selbegin!=self._bufferview._selend:
                begin = 0 if self._bufferview._selbegin==self._bufferview._viewbegin \
                    else width-(self._bufferview._viewend-self._bufferview._selbegin).total_seconds()/self._bufferview._timeprecision
                end = width if self._bufferview._selend==self._bufferview._viewend \
                    else width-(self._bufferview._viewend-self._bufferview._selend).total_seconds()/self._bufferview._timeprecision
                painter.setPen(QtCore.Qt.NoPen)
                painter.setBrush(QtGui.QColor(33, 170, 255, 100))
                painter.drawRect(begin, 1, end-begin, height)


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
    toggled = QtCore.pyqtSignal(bool)

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
            self.toggled.emit(True)
            self._parseSendOutAndWait()

    def stop(self):
        """Stop the player."""
        if self._running:
            self._running = False
            self._stopPlaying()
            self.stopped.emit()
            self.toggled.emit(False)

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
        if self.hasPendingProducts():
            # Wait until all the products have been taken before
            # saying it has finished.
            QtCore.QTimer.singleShot(0, self._finished)
        else:
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
        _toggledBusy = QtCore.pyqtSignal(bool)

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
        """Signal emitted when the recorder changes is started and stopped."""
        return self._internal.toggled

    @property
    def _toggledBusy(self):
        """Signal emitted when the recorder changes is started and stopped."""
        return self._internal._toggledBusy

    def __init__(self, request=Request.ANY,
                 timelimit=30000, sizelimit=10000, timewarping=True,
                 oversizecut=100, fps=20, guiparent=None, parent=None):
        super().__init__(request, parent=parent)
        if fps<=0: raise ValueError(
            "fps must be a value greater than zero, not %s"%str(fps))
        self.fps = fps
        self._active = False
        self._buffer= TimedProductBuffer(timelimit, sizelimit,
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
        # Player
        self._player = BufferPlayer(sender=Player.PostSender())
        self._player.stopped.connect(self._playerStopped)
        self._targets = {}
        # Setup GUI
        self._gui = Recorder.RecorderWindow(weakref.proxy(self), guiparent)
        self._gui.start.connect(self.start)
        self._gui.stop.connect(self.stop)
        self._gui.stop.connect(self._player.stop)
        self._gui.toggle.connect(self._toggle)
        self._gui.clearBuffer.connect(self.clearBuffer)
        self._gui.playTo.connect(self.playTo)
        self._gui.writeTo.connect(self.writeTo)
        self._gui.toggleKeepAlive.connect(self._toggleKeepAlive)
        self._gui.closed.connect(self.clear)
        self._toggledBusy.connect(self._gui._toggled)

    def gui(self):
        """Return the Recorder's GUI widget."""
        return self._gui

    def buffer(self):
        """Return the Recorder's product buffer."""
        return self._buffer

    def isActive(self):
        """Return whether the recorder is active."""
        return self._active

    def isBusy(self):
        """Return whether the recorder is active or it's player is
        running. When the recorder is busy users are not allowed to
        modify the buffer. """
        return self.isActive() or self._player.isRunning()

    def start(self):
        """Start product recording and product lifetime check."""
        self._setActive(True)

    def stop(self):
        """Stop product recording."""
        self._setActive(False)

    def clearBuffer(self):
        """Clear the recorder's buffer."""
        if self.isBusy(): raise RuntimeError(
            "Cannot clear the buffer while the recorder is busy.")
        else:
            self.buffer().clear()
            self.gui().bufferview.update()

    def playTo(self, uri, begin, end):
        if self.isActive():
            raise RuntimeError("The recorder is already active.")
        elif self._player.isRunning():
            raise RuntimeError("The recorder's player is already running.")
        else:
            if uri not in self._targets:
                from boing import create
                self._targets[uri] = create(uri)
                self._player.addObserver(self._targets[uri])
            self._player.setSpeed(1)
            self._player.setSender(Player.ProductSender())
            self._toggledBusy.emit(True)
            self._player.play(self.buffer().slice(begin, end))

    def writeTo(self, uri, begin, end):
        if self.isActive():
            raise RuntimeError("The recorder is already active.")
        elif self._player.isRunning():
            raise RuntimeError("The recorder's player is already running.")
        else:
            if uri not in self._targets:
                from boing import create
                self._targets[uri] = create(uri)
                self._player.addObserver(self._targets[uri])
            self._player.setSpeed(float("inf"))
            self._player.setSender(Player.PostSender())
            self._toggledBusy.emit(True)
            self._player.play(self.buffer().slice(begin, end))

    def _setActive(self, active):
        """Activate or deactivate the recorder."""
        if active!=self.isActive():
            self._active = active
            if super().request()!=Request.NONE: self.requestChanged.emit()
            if active:
                if self.timewarping and self.buffer():
                    # FIXME: this operation should be a ProductBuffer method
                    delta = datetime.datetime.now()-self._stoptime
                    for record in self.buffer():
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
            self._toggledBusy.emit(self.isBusy())

    @QtCore.pyqtSlot()
    def _toggle(self):
        """Start the recorder if it is stopped or stop it, if it is running."""
        self._setActive(not self.isActive())

    def request(self):
        """Return the recorder's request if it is active."""
        return super().request() if self.isActive() else Request.NONE

    def _consume(self, products, source):
        """If active, it appends into the buffer the received products."""
        if self.isActive():
            self.buffer().append(products)

    @QtCore.pyqtSlot()
    def _refreshtime(self):
        self.buffer().erasingTime()
        now = datetime.datetime.now()
        timelimit = self.buffer().timeLimit()
        if timelimit is None:
            # Set only the end time
            self.gui().bufferview.setEnd(now)
        else:
            # Set both begin and end time
            self.gui().bufferview.setInterval(now-timelimit, now)

    @QtCore.pyqtSlot()
    def _playerStopped(self):
        # Let the write operation end.
        QtCore.QTimer.singleShot(20, self._clearTargets)

    @QtCore.pyqtSlot()
    def _clearTargets(self):
        if not self.gui().keepalive.isChecked():
            self._player.clear()
            self._targets.clear()
        self._toggledBusy.emit(False)

    @QtCore.pyqtSlot(bool)
    def _toggleKeepAlive(self):
        if not self._player.isRunning():
            self._player.clear()
            self._targets.clear()

    class RecorderWindow(QtGui.QMainWindow, Ui_RecWindow):
        """MainWindow of the recorder tool."""

        toggle = QtCore.pyqtSignal()
        """Signal emitted when the user requires to toggle the
        recorder status."""

        start = QtCore.pyqtSignal()
        """Signal emitted when the user requires to start the product
        recording."""

        stop = QtCore.pyqtSignal()
        """Signal emitted when the user requires to stop the product
        recording or playback."""

        clearBuffer = QtCore.pyqtSignal()
        """Signal emitted when the user requires to clear the
        buffer."""

        playTo = QtCore.pyqtSignal(str, datetime.datetime, datetime.datetime)
        """Signal emitted when the user requires to write the content
        of the buffer to a target destination."""

        writeTo = QtCore.pyqtSignal(str, datetime.datetime, datetime.datetime)
        """Signal emitted when the user requires to write the content
        of the buffer to a target destination."""

        toggleKeepAlive = QtCore.pyqtSignal(bool)
        """Signal emitted when the user changes the target keep alive
        option."""

        closed = QtCore.pyqtSignal()
        """Signal emitted when the Widget is closed."""

        def __init__(self, recorder, parent=None):
            super().__init__(parent)
            self._recorder = recorder
            self.setupUi(self)
            # Graph widget
            self.bufferview = BufferView(self._recorder.buffer(),
                                         graph=Recorder.AdvancedGraph)
            self.bufferview.selectionChanged.connect(self._checkViewSelection)
            self.bufferview.viewChanged.connect(self._graphViewChanged)
            self.bufferview.graph._recorder = self._recorder
            self.bufferview.graph.customContextMenuRequested.connect(
                self.bufferview.graph._showContextMenu)
            self.bufferview.graph.clearBuffer.connect(self.clearBuffer)
            self.bufferview.graph.saveAs.connect(self._selectFileDialog)
            self.bufferview.graph.playtouri.triggered.connect(self._playToURIDialog)
            self.setCentralWidget(self.bufferview)
            # Menubar
            self.record.triggered.connect(self.start)
            self.stop_.triggered.connect(self.stop)
            self.toggle_.triggered.connect(self.toggle)
            self.quit.triggered.connect(QtGui.QApplication.instance().quit)
            self.clearselection.triggered.connect(self.bufferview.clearSelection)
            self.saveas.triggered.connect(self._selectFileDialog)
            self.playto.setMenu(QtGui.QMenu())
            self.playtouri.triggered.connect(self._playToURIDialog)
            self.keepalive.toggled.connect(self.toggleKeepAlive)
            self.selectall.triggered.connect(self.bufferview.selectAll)
            self.clear.triggered.connect(self.clearBuffer)
            # Toolbar
            self.recordtool.triggered.connect(self.start)
            self.recordtool.setIcon(QtGui.QIcon(os.path.join(_config["icons"], "record.png")))
            self.stoptool.triggered.connect(self.stop)
            self.stoptool.setIcon(QtGui.QIcon(os.path.join(_config["icons"], "stop.png")))
            # Zoom actions
            self.zoomin.triggered.connect(self.bufferview.zoomIn)
            self.zoomintool.triggered.connect(self.bufferview.zoomIn)
            self.zoomintool.setIcon(QtGui.QIcon(os.path.join(_config["icons"], "zoom-in.png")))
            self.zoomout.triggered.connect(self.bufferview.zoomOut)
            self.zoomouttool.triggered.connect(self.bufferview.zoomOut)
            self.zoomouttool.setIcon(QtGui.QIcon(os.path.join(_config["icons"], "zoom-out.png")))
            self.zoomoriginal.triggered.connect(self.bufferview.zoomOriginal)
            self.zoomoriginaltool.triggered.connect(self.bufferview.zoomOriginal)

            self.zoomoriginaltool.setIcon(QtGui.QIcon(os.path.join(_config["icons"], "zoom-original.png")))
            # Add default "play to"
            self.addTargetURI("dump:stdout")
            self.addTargetURI("viz:")
            # Play to URI dialog
            self.playtouridialog = Recorder.PlayToURIDialog()

        @QtCore.pyqtSlot(bool)
        def _toggled(self, busy):
            # Menubar
            self.record.setEnabled(not busy)
            self.stop_.setEnabled(busy)
            self.recordtool.setEnabled(not busy)
            self.stoptool.setEnabled(busy)
            self.zoomin.setEnabled(not busy)
            self.zoomout.setEnabled(self.bufferview.zoom()>1.0 and not busy)
            self.zoomoriginal.setEnabled(not busy)
            self.zoomintool.setEnabled(not busy)
            self.zoomouttool.setEnabled(self.bufferview.zoom()>1.0 and not busy)
            self.zoomoriginaltool.setEnabled(not busy)
            self.toggle_.setEnabled(not busy or self._recorder.isActive())
            for action in self.buffermenu.actions():
                action.setEnabled(not busy)
            for action in self.playto.menu().actions():
                action.setEnabled(not busy)
            self._checkViewSelection()
            # bufferview
            self.bufferview.setEnabled(not busy)
            if self._recorder.isActive(): self.bufferview.clearSelection()
            self.bufferview.graph.setContextMenuPolicy(
                QtCore.Qt.CustomContextMenu if not busy \
                    else QtCore.Qt.NoContextMenu)

        def addTargetURI(self, uri):
            assertIsInstance(uri, str)
            l = lambda action: action.text()
            if uri not in map(l, self.playto.menu().actions()):
                shortcut = "Ctrl+%s"%str(len(self.playto.menu().actions())+1) \
                    if len(self.playto.menu().actions())<9 else ""
                self.playto.menu().addAction(uri, self._playToSlot, shortcut)
                self.bufferview.graph.playto.menu().addAction(
                    uri, self._playToSlot, shortcut)

        @QtCore.pyqtSlot()
        def _checkViewSelection(self):
            busy = self._recorder.isBusy()
            begin, end = self.bufferview.selection()
            self.clearselection.setEnabled(begin!=end and not busy)
            hasselecteditems = self.bufferview.hasSelectedItems()
            self.saveas.setEnabled(hasselecteditems and not busy)
            self.playto.setEnabled(hasselecteditems and not busy)
            self.playtouri.setEnabled(hasselecteditems and not busy)
            for action in self.playto.menu().actions():
                action.setEnabled(hasselecteditems and not busy)

        @QtCore.pyqtSlot()
        def _graphViewChanged(self):
            self.zoomout.setEnabled(
                self.bufferview.zoom()>1.0 and not self._recorder.isBusy())
            self.zoomouttool.setEnabled(
                self.bufferview.zoom()>1.0 and not self._recorder.isBusy())

        @QtCore.pyqtSlot()
        def _playToSlot(self):
            self.playTo.emit(self.sender().text(), *self.bufferview.selection())

        @QtCore.pyqtSlot()
        def _selectFileDialog(self):
            """Execute a QFileDialog for selecting a target file."""
            dialog = QtGui.QFileDialog(self)
            dialog.setFileMode(QtGui.QFileDialog.AnyFile) # Existing files
            dialog.setViewMode(QtGui.QFileDialog.List)
            if not self.keepalive.isChecked():
                dialog.setAcceptMode(QtGui.QFileDialog.AcceptSave)
            if dialog.exec_():
                filepath, *useless = dialog.selectedFiles()
                sysprefix = "/" if sys.platform=="win32" else ""
                self.writeTo.emit(
                    "out.pickle.slip.file://%s%s"%(sysprefix, filepath),
                    *self.bufferview.selection())

        @QtCore.pyqtSlot()
        def _playToURIDialog(self):
            self.playtouridialog.uri.setText("")
            self.playtouridialog.uri.setFocus(QtCore.Qt.OtherFocusReason)
            if self.playtouridialog.exec_():
                self.addTargetURI(self.playtouridialog.uri.text())
                self.playTo.emit(self.playtouridialog.uri.text(),
                                 *self.bufferview.selection())

        def closeEvent(self, event):
            self.closed.emit()
            super().closeEvent(event)

    class AdvancedGraph(BufferView.Graph):
        """Widget showing the content of the buffer."""

        clearBuffer = QtCore.pyqtSignal()
        """Signal emitted when the user requires to clear the
        buffer."""

        saveAs = QtCore.pyqtSignal()
        """Signal emitted when the user requires to save the
        buffer."""

        def __init__(self, bufferview, parent=None):
            super().__init__(bufferview, parent)
            self._bufferview.selectionChanged.connect(self._checkViewSelection)
            # Init context menu
            self.menu = QtGui.QMenu(self)
            self.menu.addAction(
                "Select All", self._bufferview.selectAll, "Ctrl+A")
            self.clearselection = QtGui.QAction("Clear Selection", self.menu)
            self.clearselection.triggered.connect(self._bufferview.clearSelection)
            self.clearselection.setShortcut("Esc")
            self.menu.addAction(self.clearselection)
            self.menu.addSeparator()
            self.saveas = QtGui.QAction("Save as...", self.menu)
            self.saveas.triggered.connect(self.saveAs)
            self.saveas.setShortcut("Ctrl+S")
            self.menu.addAction(self.saveas)
            self.menu.addSeparator()
            self.playto = QtGui.QAction("Play To", self.menu)
            self.playto.setMenu(QtGui.QMenu())
            self.menu.addAction(self.playto)
            self.playtouri = QtGui.QAction("Play to URI...", self.menu)
            self.playtouri.setShortcut("Ctrl+U")
            self.menu.addAction(self.playtouri)
            self.menu.addSeparator()
            self.menu.addAction("Clear buffer", self.clearBuffer, "Ctrl+C")

        @QtCore.pyqtSlot()
        def _checkViewSelection(self):
            begin, end = self._bufferview.selection()
            self.clearselection.setEnabled(begin!=end)
            hasselecteditems = self._bufferview.hasSelectedItems()
            self.saveas.setEnabled(hasselecteditems)
            self.playto.setEnabled(hasselecteditems)
            self.playtouri.setEnabled(hasselecteditems)
            for action in self.playto.menu().actions():
                action.setEnabled(hasselecteditems)

        @QtCore.pyqtSlot(QtCore.QPoint)
        def _showContextMenu(self, pos):
            """Display the context menu if the recorder is not busy."""
            self.menu.exec_(self.mapToGlobal(pos))

        def paintEvent(self, event):
            super().paintEvent(event)
            if self._recorder.isBusy():
                painter = QtGui.QPainter(self)
                painter.setPen(QtCore.Qt.NoPen)
                color = QtGui.QColor(self.palette().dark())
                color.setAlpha(100)
                painter.setBrush(color)
                painter.drawRect(2, 2, self.width()-4, self.height()-4)
                if self._recorder.isActive():
                    painter.setFont(QtGui.QFont( "courier", 9))
                    painter.setPen(QtCore.Qt.black)
                    painter.drawText(self.width()-25, 12, "REC")
                    painter.setPen(QtCore.Qt.red)
                    painter.setBrush(QtCore.Qt.red)
                    painter.drawEllipse(self.width()-34, 5, 6, 6)

    class PlayToURIDialog(QtGui.QDialog, Ui_PlayToURIDialog):
        def __init__(self):
            super().__init__()
            self.setupUi(self)
