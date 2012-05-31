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

import boing

import boing.utils as utils
import boing.utils.fileutils as fileutils
from boing.core.MappingEconomy \
    import HierarchicalProducer, HierarchicalConsumer, Node
from boing.core.OnDemandProduction import OnDemandProducer

# Compile all .ui files in this directory
uic.compileUiDir(os.path.dirname(__file__))
from boing.nodes.uiRecorder import Ui_recorder
#from boing.nodes.uiUrlDialog import Ui_UrlDialog

'''
class ProductBuffer(QtCore.QObject):

    """Emitted anytime the product buffer changes."""
    changed = QtCore.pyqtSignal()
    
    """Emitted when the maximum number of products has been exceeded
    and some products must be dropped before the normal product's
    lifetime."""
    productDrop = QtCore.pyqtSignal()

    def __init__(self, sizelimit=10000, oversizecut=100, parent=None, **kwargs):
        super().__init__(parent)
        """Product buffer."""
        self._buffer = []
        """Number of products stored in buffer."""
        self._sum = 0
        """Maximum number of stored products."""
        self._sizelimit = sizelimit
        """When stored products exceed 'sizelimit', instead of keeping
        'sizelimit' products, it keeps 'sizelimit'-'oversizecut'
        products, so that productDrop is not invoked anytime a new
        product is obtained."""
        self.oversizecut = oversizecut
        # Connect argument slot
        for key, value in kwargs.items():
            if key=="changed": self.changed.connect(value)
            elif key=="productDrop": self.productDrop.connect(value) 
            else: raise TypeError(
                "'%s' is an invalid keyword argument for this function"%key)
                
    def append(self, products):
        """Store products as a buffer item."""
        record = utils.quickdict()
        record.timetag = datetime.datetime.now()
        record.products = products
        self._buffer.append(record)
        self._sum += len(products)
        # Check maximum number of products
        if self._sum>self._sizelimit:
            count = 0
            for i, record in enumerate(self._buffer):
                count += len(record.products)
                if count>=self.oversizecut: break
            del self._buffer[:i+1]
            self._sum -= count
            self.productDrop.emit()
        self.changed.emit()

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

    def sizeLimit(self):
        return self._sizelimit

    def setSizeLimit(self, sizelimit):
        self._sizelimit = sizelimit
        

    def __len__(self):
        """Return the number of elements of the buffer."""
        return len(self._buffer)

    def __getitem__(self, index):
        return self._buffer[index]

    def __delitem__(self, index):
        del self._buffer[index]

    def __iter__(self):
        return iter(self._buffer)

    def index(self, timetag, start=0, end=None):
        """Index of the first element with timetag greater or equal
        than 'timetag' or len(self) if there is no such item."""
        if end is None: end = len(self._buffer)
        for i in range(start, end):
            if self._buffer[i].timetag>=timetag: break
        else: 
            i += 1
        return i

    def slice(self, starttime=None, endtime=None):
        """Return a slice of the buffer's elements. 'starttime' and
        'endtime' must be datetime.datetime or None and they can be
        used to slice the buffer."""
        if starttime is None: start = 0
        elif not isinstance(starttime, datetime.datetime):
            raise TypeError(
                "'starttime' must be datetime.datetime or None, not %s"\
                    %type(starttime))
        else: start = self.index(starttime)
        if endtime is None: end = len(self._buffer)
        elif not isinstance(endtime, datetime.datetime):
            raise TypeError(
                "'endtime' must be datetime.datetime or None, not %s"%type(endtime))
        else: end = self.index(endtime, start)
        return collections.deque(self._buffer[start:end])

    def islice(self, starttime=None, endtime=None):
        """Returns an iterator over the stored records {'timetag':
        ... , 'products': ...}.  'starttime' and 'endtime' must be
        datetime.datetime or None and they can be used to slice the
        buffer."""
        if starttime is not None and not isinstance(starttime, datetime.datetime):
            raise TypeError(
                "'starttime' must be datetime.datetime or None, not %s"\
                    %type(starttime))
        if endtime is not None and not isinstance(endtime, datetime.datetime):
            raise TypeError(
                "'endtime' must be datetime.datetime or None, not %s"%type(endtime))
        for record in self._buffer:            
            if starttime is not None and record.timetag<starttime: continue
            if endtime is not None and record.timetag>endtime: break
            yield record


class TimedProductBuffer(ProductBuffer):
    """Elements have a fixed timelife and they are automatically
    removed when they are done."""
    def __init__(self, timelimit=30000, sizelimit=10000, eraserinterval=1000, 
                 oversizecut=100, parent=None, **kwargs):
        super().__init__(sizelimit, oversizecut, parent, **kwargs)
        """Products timelife."""
        self._timelimit = None if timelimit is None or timelimit==float("inf") \
            else datetime.timedelta(milliseconds=timelimit)
        """Innovation timer timeout inverval."""
        self._eraserinterval = eraserinterval
        """Product timelife verifier."""
        self._eraser = QtCore.QTimer(timeout=self._erasingTime)
        if self._timelimit is not None: self._eraser.start(self._eraserinterval)

    def timeLimit(self):
        return self._timelimit

    def setTimeLimit(self, msec):
        self._timelimit = None if msec is None or msec==float("inf") \
            else datetime.timedelta(milliseconds=msec)
        self.stop() if self._timelimit is None else self.start()

    def eraserInterval(self):
        return self._eraser.interval()

    def setEraserInterval(self, msec):
        self._eraser.setInterval(msec)

    def isEraserActive(self):
        return self._eraser.isActive()

    def setEraserActive(self, active):
        if active and self._timelimit is not None:
            self._eraser.start(self._eraserinterval)
        else:
            self._eraser.stop()

    def _erasingTime(self):
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

class ProductBufferGraph(QtGui.QWidget):

    def __init__(self, buffer, starttime=None, endtime=None, 
                 fps=None, parent=None):
        super().__init__(parent)
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
        return self._starttime

    def setStartTime(self, starttime):
        self._starttime = starttime if starttime is not None \
            else datetime.datetime.min
        self._interval = self._endtime-self._starttime
        self.update()

    def endTime(self):
        return self._endtime

    def setEndTime(self, endtime):
        self._endtime = endtime if endtime is not None \
            else datetime.datetime.max
        self._interval = self._endtime-self._starttime
        self.update()

    def fps(self):
        return 0 if not self._refresher.isActive() \
            else 1/self._refresher.interval()

    def setFps(self, fps):
        if fps is None or fps==0: 
            self._refresher.stop()
            if self._refresher.isActive():
                self._buffer.changed.disconnect(self._bufferChanged)
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
        # # Draw rec point
        # if self._buffer.isRunning():
        #     painter.drawText(width-25,10, "REC")
        #     painter.save()
        #     painter.setPen(QtCore.Qt.red)
        #     painter.setBrush(QtCore.Qt.red)
        #     painter.drawEllipse(width-34, 3, 6, 6)
        #     painter.restore()
        # Draw products
        if self._buffer and self._interval!=datetime.timedelta():
            for record in self._buffer.islice(self._starttime, self._endtime):
                dx = (self._endtime-record.timetag)/self._interval*width
                painter.drawLine(width-dx, height, width-dx, height-30)

# -------------------------------------------------------------------

class Recorder(HierarchicalConsumer, QtCore.QObject):
    
    started = QtCore.pyqtSignal()
    stopped = QtCore.pyqtSignal()

    def __init__(self, timelimit=30000, sizelimit=10000, timewarping=True,
                 oversizecut=100, fps=60, guiparent=None, parent=None,
                 *args, **kwargs):
        HierarchicalConsumer.__init__(self, *args, **kwargs)
        QtCore.QObject.__init__(self, parent)
        self.__active = True
        self.__buffer = TimedProductBuffer(timelimit, sizelimit, 
                                           1000/fps, oversizecut)
        """If True, the time when the buffer is stopped, it does not
        reduce products timelife."""
        self.timewarping = timewarping
        self._stoptime = None
        self.fps = fps
        self.gui = Recorder._Ui(weakref.proxy(self), guiparent)
        self.gui.recorderToggled(True)
        self._refresher = QtCore.QTimer(timeout=self.refreshtime)
        self._refresher.start(1000/self.fps)
        # FIXME: When buffer is not running request should be set to None
        self.__writer = BufferPlayer(self.__buffer)
        self.__writer.setSpeed(float("inf"))
        self.__writer.stopped.connect(self._writerStopped)
        self.__target = None

    def buffer(self):
        return self.__buffer

    def isActive(self):
        return self.__active

    def setActive(self, active):
        self.start() if active else self.stop()

    def start(self):
        """Start product recording and product lifetime check."""
        if not self.__active:
            self.__active = True
            if self.timewarping:
                delta = datetime.datetime.now()-self._stoptime
                for record in self.__buffer:
                    record.timetag += delta
                # self.changed.emit()
            self._stoptime = None
            self.__buffer.setEraserActive(True)
            self._refresher.start(1000/self.fps)
            self.started.emit()

    def stop(self):
        """Stop product recording, so that it will not store any other product 
        and it will not loose any stored product."""
        if self.__active:
            self.__buffer.setEraserActive(False)
            self.__active = False
            self._stoptime = datetime.datetime.now()
            self._refresher.stop()
            self.stopped.emit()
            
    def _consume(self, products, source):
        if self.__active:
            self.__buffer.append(products)

    def refreshtime(self):
        now = datetime.datetime.now()
        timelimit = self.__buffer.timeLimit()
        if timelimit is not None:                    
            self.gui.graph.setStartTime(now-timelimit)
        self.gui.graph.setEndTime(now)

    def writeTo(self, url):
        if not self.__writer.isRunning():
            self.__target = boing.create(url)
            self.__writer.addObserver(self.__target)
            self.gui.writerToggled(True)
            self.__writer.start()
        else:
            raise Exception("Recorder's writer is already running.")
    
    def _writerStopped(self):
        self.__target = None
        self.gui.writerToggled(False)
            
    class _Ui(QtGui.QWidget, Ui_recorder):
    
        def __init__(self, recorder, parent=None):
            super().__init__(parent)
            recorder.started.connect(lambda: self.recorderToggled(True))
            recorder.stopped.connect(lambda: self.recorderToggled(False))
            now = datetime.datetime.now()
            self.graph = ProductBufferGraph(recorder.buffer(), now, now)
            self.graph.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            # Setup ui
            self.setupUi(self)          
            self.framelayout.addWidget(self.graph)
            self.startstop.toggled.connect(recorder.setActive)
            QtGui.QShortcut(
                'Ctrl+Q', self, activated=QtGui.QApplication.instance().quit)
            # self.graph.menu.aboutToShow.connect(
            #     self.menuOn, QtCore.Qt.QueuedConnection)
            # self.graph.menu.aboutToHide.connect(
            #     self.menuOff, QtCore.Qt.QueuedConnection)
            # self.graph.urldialog.finished.connect(
            #     self.menuOff, QtCore.Qt.QueuedConnection)
            # Init context menu
            # self.actionurls = set()
            self.contextmenu = QtGui.QMenu(self)
            self.contextmenu.addAction("Start", recorder.start)
            self.contextmenu.addAction("Stop", recorder.stop)
            self.contextmenu.addSeparator()
            self.contextmenu.addAction(
                "Write to stdout", 
                lambda: recorder.writeTo("dump:stdout?request=timetag|products"))
            
            #self.contextmenu.addAction("Write to file", 
            #                           FIXME!)
            self.contextmenu.addSeparator()
            self.contextmenu.addAction("Clear", recorder.buffer().clear)
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

        def recorderToggled(self, active):
            self.startstop.setChecked(active)
            self.graph.setFps(0 if active else 60)            
            for action in self.contextmenu.actions():
                if not action.isSeparator():
                    if action.text()=="Stop":
                        action.setEnabled(active)
                    else: 
                        action.setEnabled(not active)

        def writerToggled(self, active):
            self.startstop.setEnabled(not active)
            self.graph.setContextMenuPolicy(QtCore.Qt.NoContextMenu if active \
                                                else QtCore.Qt.CustomContextMenu)

        '''def menuOn(self):
            if self.stopplay.isChecked():
                self.stopplay.setChecked(False)
                self.menustop = True
        
        def menuOff(self):
            if self.menustop and not self.graph.urldialog.isVisible():
                self.stopplay.setChecked(True)
                self.menustop = False'''

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
                self.buffer.forwardTo(self.urldialog.url.text())

        

# -------------------------------------------------------------------

class BasePlayer(HierarchicalProducer):

    @staticmethod
    def PostSender(player, obj):
        player._postProduct(obj)

    @staticmethod
    def ProductSender(player, obj):
        for product in obj.products:
            if player._tag("timetag"):
                product["timetag"] = player._date if player._date is not None \
                    else datetime.datetime.now()
            player._postProduct(product)

    started = QtCore.pyqtSignal()
    stopped = QtCore.pyqtSignal()
    
    def __init__(self, parser, sender, speed=1.0, loop=False, interval=1000, 
                 parent=None):
        super().__init__(parent=parent)
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
        self._addTag("timetag", {"timetag": datetime.datetime.now()})

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


class FilePlayer(BasePlayer):

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
                 parser=FileParser(), sender=BasePlayer.PostSender, 
                 speed=1.0, loop=False, interval=1000, parent=None):
        super().__init__(parser, sender, speed, loop, interval, parent)
        self.__fd = fileutils.File(filepath, uncompress=True)

    def file(self):
        return self.__fd

    def stop(self):
        super().stop()
        if self.__fd.isOpen(): self.__fd.seek(0)


'''class BufferPlayer(BasePlayer):
      
    class ListParse(BasePlayer.BaseFunctor):
        def __init__(self, player):
            super().__init__(player)
            self.player.started.connect(self._playerStarted)

        def _playerStarted(self):
            self.index = 0

        def __call__(self):
            rvalue = False
            if self.index<len(self.player._buffer):
                self.player._queue.append(self.player._buffer[self.index])
                self.index += 1
                rvalue = True
            return rvalue

    def __init__(self, buffer, parse=ListParse, sendout=BasePlayer.PostSendOut, 
                 speed=1.0, loop=False, parent=None):
        super().__init__(parse, sendout, speed, loop, parent)
        self._buffer = buffer
        
class ProductPlayer(AbstractPlayer):
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
