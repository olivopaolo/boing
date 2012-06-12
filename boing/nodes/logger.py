# -*- coding: utf-8 -*-
#
# boing/nodes/logger.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import datetime
import math
import os
import weakref

from PyQt4 import QtCore, QtGui, uic

from boing import Offer, Request, Producer, Consumer
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
        self._sizelimit = assertIsInstance(sizelimit, int)
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
        self._sizelimit = sizelimit
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

    @staticmethod
    def PostSender(player, obj):
        player.postProduct(obj)

    @staticmethod
    def ProductSender(player, obj):
        for product in obj.products:
            #product["timetag"] = player._date if player._date is not None \
            #    else datetime.datetime.now()
            player.postProduct(product)

    started = QtCore.pyqtSignal()
    stopped = QtCore.pyqtSignal()
    
    def __init__(self, parser, sender, speed=1.0, loop=False, interval=1000, 
                 offer=Offer(Offer.UndefinedProduct()), parent=None):
        super().__init__(offer, parent=parent)
        self._parser = parser
        self._sender = sender
        if not isinstance(loop, bool): raise TypeError(
            "loop must be boolean, not '%s'"%loop.__class__.__name__)
        self._loop = loop
        self._speed = float(speed)
        self._interval = int(interval)
        self._queue = collections.deque()
        self.__waittimer = QtCore.QTimer(timeout=self._parseSendOutAndWait)
        self.__waittimer.setSingleShot(True)
        self.__looptimer = QtCore.QTimer(timeout=self.start)
        self.__looptimer.setSingleShot(True)
        self._running = False
        self._date = None # Datetime when the next item should be sent.
        self.playcnt = 0

    def start(self):
        if not self._running:
            self._running = True
            self.playcnt += 1
            self.started.emit()
            self._parseSendOutAndWait()
        
    def stop(self):
        if self._running:
            self._running = False
            self.__waittimer.stop()
            self._queue.clear()
            self._date = None
            self.stopped.emit()

    def isRunning(self):
        return self._running

    def isLooping(self):
        return self._loop

    def speed(self):
        return self._speed

    def setSpeed(self, speed):
        self._speed = speed

    def _parse(self):
        return self._parser(self)

    def _sendOut(self, obj):
        return self._sender(self, obj)

    def setSender(self, sender):
        self._sender = assertIsInstance(sender, collections.Callable)

    def _parseSendOutAndWait(self):
        # Parse for the first
        while not self._queue and self._parse(): pass
        if not self._queue: self.stop()
        else:
            # Send out the first
            first = self._queue.popleft()
            sendtime = datetime.datetime.now()
            self._sendOut(first)
            # Parse for the second
            while not self._queue and self._parse(): pass
            if not self._queue: 
                self.stop()
                if self._loop: self.__looptimer.start(self._interval)
                else:
                    # FIXME: Handle how to notify that a log is terminated
                    # self._sendOut(None)
                    pass
            else:
                # Wait for the second
                if math.isinf(self._speed): msec = 0
                else:
                    delta = (self._queue[0].timetag-first.timetag)/self._speed
                    if self._date is not None: delta -= sendtime-self._date
                    self._date = sendtime+delta
                    msec = 0 if delta.days<0 else delta.total_seconds()*1000
                self.__waittimer.start(msec)

class FilePlayer(Player):

    class FileParser(collections.Callable):
        def __init__(self, decoder=None):
            self.decoder = decoder if isinstance(decoder, collections.Callable) \
                else lambda obj: obj

        def __call__(self, player):
            rvalue = False
            if player.file().isOpen(): 
                encoded = player.file().read()
                if encoded:
                    player._queue.extend(self.decoder(encoded))
                    rvalue = True
            return rvalue

    def __init__(self, filepath,
                 parser=FileParser(), sender=Player.PostSender, 
                 speed=1.0, loop=False, interval=1000, 
                 offer=Offer(Offer.UndefinedProduct()), parent=None):
        super().__init__(parser, sender, speed, loop, interval, offer, parent)
        self.__fd = fileutils.File(filepath, uncompress=True)

    def file(self):
        return self.__fd

    def stop(self):
        super().stop()
        if self.__fd.isOpen(): self.__fd.seek(0)


class BufferPlayer(Player):
      
    class ListParser(collections.Callable):
        def __init__(self):
            super().__init__()
            self.index = 0

        def reset(self): self.index = 0

        def __call__(self, player):
            rvalue = False
            if self.index<len(player._buffer):
                player._queue.append(player._buffer[self.index])
                self.index += 1
                rvalue = True
            return rvalue

    def __init__(self, parse=ListParser(), sendout=Player.PostSender, 
                 speed=1.0, loop=False, interval=1000,
                 offer=Offer(Offer.UndefinedProduct()), parent=None):
        super().__init__(parse, sendout, speed, loop, interval, offer, parent)
        self._buffer = tuple()

    def start(self, buffer):
        if not self._running:
            self._buffer = buffer
            super().start()

    def stop(self):
        super().stop()
        self._parser.reset()

        
'''class ProductPlayer(AbstractPlayer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._addTag("timetag", {"timetag": datetime.datetime.now()})

    def _sendOut(self, next):
        for product in next.products:
            if self._tag("timetag"):
                product["timetag"] = self._date if self._date is not None \
                    else datetime.datetime.now()
            self._postProduct(product)


class ProductQueuePlayer(ProductPlayer):
    def __init__(self, buffer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__buffer = buffer
        
    def _parse(self):
        rvalue = False
        if self.__buffer:
            if hasattr("popleft", self.__buffer):                
                self._queue.append(self.__buffer.popleft())
            else:
                self._queue.append(self.__buffer.pop(0))
            rvalue = True
        return rvalue


class ProductListPlayer(ProductPlayer):
    def __init__(self, buffer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__buffer = buffer

    def start(self):
        self.__index = 0
        super().start()

    def _parse(self):
        rvalue = False
        if self.__index<len(self.__buffer):
            self._queue.append(self.__buffer[self.__index])
            self.__index += 1
            rvalue = True
        return rvalue
'''

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
        self._writer = BufferPlayer()
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
            self._writer.setSender(BufferPlayer.PostSender)
            self._writer.start(self._buffer)
        else:
            raise Exception("Recorder's writer is already running.")

    def playTo(self, uri):
        if not self._writer.isRunning():
            from boing import create
            self._writer.addObserver(create(uri, mode="out"), child=True)
            self._writer.setSpeed(1)
            self._writer.setSender(BufferPlayer.ProductSender)
            self._writer.start(self._buffer)
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
