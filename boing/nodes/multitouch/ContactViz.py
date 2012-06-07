# -*- coding: utf-8 -*-
#
# boing/nodes/multitouch/ContactViz.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import copy
import datetime
import math
import weakref

from PyQt4 import QtCore, QtGui

from boing import Request, Consumer
from boing.core.StateMachine import StateMachine
from boing.utils import quickdict, deepDump

#import uiVizConfig

class ContactViz(Consumer):

    '''"""Gestures' position is fit to the widget size"""
    WINSIZE = 1
    """Input device ratio is respected (if possible)"""
    RATIOSIZE = 2
    """SI device size is respected (if possible)"""
    SISIZE = 3'''
            
    def __init__(self, antialiasing=False, fps=60, parent=None):
        super().__init__(request=Request("diff.*.contacts|source"), 
                       hz=fps, parent=parent)
        self._sources = {}
        self.__gui = ContactWidget(weakref.proxy(self), antialiasing)
        self.__gui.show()
        '''self.__display = DisplayDevice.create()
        if self.__display.url.scheme=="dummy": 
            print("WARNING: using dummy DisplayDevice")
            self.__display.debug()
        self.drawmode = ContactViz.SISIZE'''

    def _consume(self, products, producer):
        for product in products:
            if "diff" in product:
                source = product.get("source", id(producer))
                record = self._sources.setdefault(
                    source, quickdict({"state":StateMachine()}))
                # Update state
                record.state.applyDiff(product["diff"])
                # Update history
                history = record.history
                for key, event in product["diff"].items():
                    if key in ("added", "updated"):
                        for gid, value in event.contacts.items():
                            track = history.setdefault(gid, [])
                            if track or "rel_pos" in value: track.append(value)
                    elif key=="removed":
                        for key in event.contacts:
                            history.pop(key, None)
                    else:
                        raise ValueError("Unexpected diff key: %s", key)
                self.__gui.update()


class ContactWidget(QtGui.QWidget):

    '''class ConfigPanel(QtGui.QDialog, uiVizConfig.Ui_ConfigPanel):
        """Configuration panel for the ContactViz properties."""
        def __init__(self, current):
            QtGui.QDialog.__init__(self)
            self.setupUi(self)
            if current==ContactViz.WINSIZE:
                self.winsize.setChecked(True)
            elif current==ContactViz.RATIOSIZE:
                self.ratiosize.setChecked(True)
            elif current==ContactViz.SISIZE:
                self.sisize.setChecked(True)

        def drawmode(self):
            """Return the selected drawmode."""
            if self.winsize.isChecked():
                return ContactViz.WINSIZE
            elif self.ratiosize.isChecked():
                return ContactViz.RATIOSIZE
            elif self.sisize.isChecked():
                return ContactViz.SISIZE
            else:
                return ContactViz.SISIZE'''


    def __init__(self, node, antialiasing=False, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.node = node
        # Setup GUI
        if not isinstance(antialiasing, bool): raise TypeError(
            "antialiasing must be boolean, not '%s'"%antialiasing.__class__.__name__)
        self.antialiasing = antialiasing
        self.setWhatsThis("Event &Viz")
        self.sizehint = QtCore.QSize(320,240)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        '''self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.connect(self, QtCore.SIGNAL("customContextMenuRequested(const QPoint &)"), self.__contextmenu)
        self.connect(QtGui.QShortcut('Alt+C', self), QtCore.SIGNAL("activated()"), self.__configpanel)'''
        ctrlQ = QtGui.QShortcut('Ctrl+Q', self)
        ctrlQ.activated.connect(QtGui.QApplication.instance().quit)
        """position circle size"""
        self.phi = 4 
        self.__fps_count = 0
        self.__fps_previous = 0
        self.__fps_timer = QtCore.QTimer()
        self.__fps_timer.timeout.connect(self._fpsTimeout)
        self.debuglevel = 0
        self.oldest = None

    def paintEvent(self, event):
        width, height = self.width(), self.height()
        count = 0
        if self.debuglevel>3: timer = QtCore.QElapsedTimer() ; timer.start();
        # Setup painter
        painter = QtGui.QPainter(self)
        if self.antialiasing: painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setFont(QtGui.QFont( "courier", 9))
        # Draw grid
        painter.setPen(QtGui.QColor(200,200,200))
        for i in range(0, 100, 10):
            x = i*width/100
            y = i*height/100
            painter.drawLine(0, y, width, y)
            painter.drawLine(x, 0, x, height)
        # Draw contacts
        for source, record in self.node._sources.items():
            fill, outline = record.get("color",
                                       (QtCore.Qt.gray, QtCore.Qt.black))
            deviceratio = None
            """contactstate = source.contacts.get("contacts", {})
            pos_si_range = contactstate.get("pos_si_range")
            if pos_si_range is not None:
                deviceratio = float(pos_si_range[0])/pos_si_range[1] 
            else: deviceratio = None
            if pos_si_range and self.drawmode!=ContactViz.WINSIZE:
                # Draw device area
                if self.drawmode==ContactViz.SISIZE:
                    pixel_pos_range = self.__display.mm2pixels([i*1000 for i in pos_si_range])
                else:
                    width, height = self.width(), self.height()
                    vizratio = float(width) / height
                    if vizratio>deviceratio: width = float(height)*deviceratio
                    else: height = float(width) / deviceratio
                    pixel_pos_range = (width, height)
                painter.save()
                pen = QtGui.QPen(fill, 6, QtCore.Qt.CustomDashLine)
                pen.setDashPattern([3, 5])
                painter.setPen(pen)
                painter.setBrush(QtCore.Qt.NoBrush)
                painter.drawRect(0, 0, pixel_pos_range[0], pixel_pos_range[1])
                painter.restore()"""
            painter.setPen(outline)
            painter.setBrush(fill)
            # Draw tracks
            for gid, stateN in record.state.state().contacts.items():
                #gid, history in record.history.items():
                #stateN = record.contacts.history[gid]
                if "rel_pos" not in stateN: continue
                posN = self.__tovizpos(stateN.rel_pos, deviceratio)
                x, y = posN
                history = record.history.setdefault(gid, [])
                if len(history)>1:
                    # Draw first point
                    pos0 = self.__tovizpos(history[0].rel_pos, deviceratio)
                    painter.save()
                    painter.setBrush(outline)
                    painter.drawEllipse(pos0[0]-3, pos0[1]-3, 6, 6)
                    painter.restore()
                    # Draw path
                    path = QtGui.QPainterPath()
                    path.moveTo(*pos0);
                    posI = pos0
                    for memento in history[1:]:
                        if "rel_pos" in memento: 
                            posI = memento.rel_pos
                            posI = self.__tovizpos(posI, deviceratio)
                            path.lineTo(*posI)
                            count += 1
                    painter.strokePath(path, painter.pen())
                # Draw boundingbox if defined                
                if "boundingbox" in stateN \
                        and "rel_size" in stateN.boundingbox:
                    bb = stateN.boundingbox
                    bb_rel_size = bb.rel_size
                    bb_angle = bb.get("si_angle")
                    bb_x, bb_y = (x, y) if "rel_pos" not in bb \
                        else self.__tovizpos(bb.rel_pos, deviceratio)
                    painter.save()
                    painter.setPen(QtGui.QPen(fill, 2))
                    bb_brush_color = QtGui.QColor(fill)
                    bb_brush_color.setAlphaF(0.5)
                    painter.setBrush(bb_brush_color)
                    painter.translate(bb_x, bb_y)
                    if bb_angle is not None: 
                        painter.rotate(bb_angle[0]*180/math.pi)
                    painter.drawEllipse(QtCore.QPoint(0,0),
                                        int(bb_rel_size[0] * width),
                                        int(bb_rel_size[1] * height))     
                    painter.restore()
                # Draw objclass if defined
                if "objclass" in stateN:
                    painter.drawText(x+1.5*o, y-2*o, "obj: %d"%stateN.objclass)
                # Draw orientation if defined
                if "si_angle" in stateN:
                    painter.save()
                    pencolor = QtGui.QColor(fill)
                    pencolor.setAlphaF(0.4)
                    painter.setPen(QtGui.QPen(pencolor, 16))
                    l = 10
                    angle = stateN.si_angle[0]
                    dx = math.cos(angle) * l
                    dy = math.sin(angle) * l
                    painter.drawLine(x-dx, y-dy, x+dx, y+dy)           
                    painter.restore()
                # Draw speed if defined
                if "rel_speed" in stateN:
                    painter.save()
                    pencolor = QtGui.QColor(fill)
                    pencolor.setAlphaF(0.85)
                    pen = QtGui.QPen(pencolor, 4)
                    pen.setCapStyle(QtCore.Qt.RoundCap)
                    painter.setPen(pen)
                    l = 25
                    X, Y = self.__tovizpos(stateN.rel_speed, deviceratio)
                    painter.drawLine(x, y, x+X*0.5, y+Y*0.5)           
                    painter.restore()
                # Draw current position
                count += 1
                painter.drawEllipse(x-self.phi, y-self.phi, 
                                    2*self.phi, 2*self.phi)

                # Print additional information
                if self.debuglevel>0:
                    painter.setPen(QtCore.Qt.black)
                    painter.drawText(x+1.5*self.phi, y+self.phi, 
                                     "%s (%s)"%(gid, len(history)))
                    if self.debuglevel>1:
                        i = 1 ;
                        xx = x+1.5*self.phi
                        yy = y+self.phi+i*10
                        painter.drawText(
                            xx, yy,
                            "%.3f,%.3f (rel_pos)"%(
                                stateN.rel_pos[0], stateN.rel_pos[1]))
                        if "rel_speed" in stateN:
                            i += 1 ;
                            xx = x+1.5*self.phi
                            yy = y+self.phi+i*10
                            painter.drawText(
                                xx, yy,
                                "%+.3f,%+.3f (rel_speed)"%(
                                    stateN.rel_speed[0], stateN.rel_speed[1]))
                        if "si_angle" in stateN:
                            i += 1 ;
                            xx = x+1.5*self.phi
                            yy = y+self.phi+i*10
                            painter.drawText(
                                xx, yy,
                                "%+.3f (si_angle)"%(stateN.si_angle[0]))
                        if self.debuglevel>2:
                            i += 1
                            xx = x+1.5*self.phi
                            yy = y+self.phi+i*10
                            painter.drawText(xx, yy, "%s (source)"%source)
        if self.debuglevel>3:
            painter.setPen(QtCore.Qt.black)
            ntracks = nsources = 0
            for record in self.node._sources.values():
                ntracks = ntracks + len(record.history)
                nsources += 1
            painter.drawText(5,10,
                             "%d sources; %d tracks; %d points;  %d ms"\
                                 %(nsources, ntracks, count, timer.elapsed()))
            if self.oldest is not None:
                lag = datetime.datetime.now()-self.oldest
                msecs = lag.seconds*1000+lag.microseconds/1000
                painter.drawText(5, 20, "lag: %d msecs"%msecs)
            self.__fps_count += 1
            painter.drawText(5, height-5, "fps: %d Hz"%self.__fps_previous)
        self.oldest = None
                
    def keyPressEvent(self, event):
        key = event.key()
        if key==QtCore.Qt.Key_Space:
            self.debuglevel = (self.debuglevel + 1) % 5
            if self.debuglevel>3:
                self.__fps_count = 0
                self.__fps_timer.start(1000)
            else:
                self.__fps_timer.stop()
            self.update()
        else: QtGui.QWidget.keyPressEvent(self, event)
        
    def sizeHint(self):
        return self.sizehint

    def __tovizpos(self, event, deviceratio=None):
        """Return the coordinates in pixel for the specified event
        of None if it can't be determined."""
        rvalue = None
        """if self.drawmode==ContactViz.SISIZE:
            rvalue = event.get("pixel_pos")
        elif self.drawmode==ContactViz.RATIOSIZE and deviceratio is not None:
            width, height = self.width(), self.height()
            vizratio = float(width) / height
            if vizratio>deviceratio: width = float(height) * deviceratio
            else: height = float(width) / deviceratio
            pos = event.get("rel_pos")
            if pos is None: return None
            else:
                rvalue = list(pos)
                rvalue[0] *= width
                rvalue[1] *= height"""
        if rvalue is None:
            pos = event#.get("rel_pos")
            if pos is not None:
                rvalue = list(pos[:2])
                rvalue[0] *= self.width()
                rvalue[1] *= self.height()
        return rvalue

    def _fpsTimeout(self):
        self.__fps_previous = self.__fps_count
        self.__fps_count = 0
        self.update()
    
    '''
    def __contextmenu(self, pos):
        """Show the context menu."""
        menu = QtGui.QMenu(self)        
        showconf = QtGui.QAction('Show config panel', menu) ;
        self.connect(showconf, QtCore.SIGNAL("triggered()"), self.__configpanel)
        menu.addAction(showconf)
        menu.exec_(self.mapToGlobal(pos))

    def __configpanel(self):
        """Show the configuration panel."""
        config = ContactViz.ConfigPanel(self.drawmode)
        if config.exec_():
            self.drawmode = config.drawmode()
            self.update()'''
