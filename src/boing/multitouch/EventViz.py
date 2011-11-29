# -*- coding: utf-8 -*-
#
# boing/multitouch/EventViz.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from PyQt4 import QtCore, QtGui

from boing.eventloop.OnDemandProduction import SelectiveConsumer
from boing.eventloop.StateMachine import StateMachine
from boing.utils.ExtensibleTree import ExtensibleTree

#import uiVizConfig

class EventViz(QtGui.QWidget, SelectiveConsumer):

    """Gestures' position is fit to the widget size"""
    WINSIZE = 1
    """Input device ratio is respected (if possible)"""
    RATIOSIZE = 2
    """SI device size is respected (if possible)"""
    SISIZE = 3
    '''
    class ConfigPanel(QtGui.QDialog, uiVizConfig.Ui_ConfigPanel):
        """Configuration panel for the eventviz properties."""
        def __init__(self, current):
            QtGui.QDialog.__init__(self)
            self.setupUi(self)
            if current==EventViz.WINSIZE:
                self.winsize.setChecked(True)
            elif current==EventViz.RATIOSIZE:
                self.ratiosize.setChecked(True)
            elif current==EventViz.SISIZE:
                self.sisize.setChecked(True)

        def drawmode(self):
            """Return the selected drawmode."""
            if self.winsize.isChecked():
                return EventViz.WINSIZE
            elif self.ratiosize.isChecked():
                return EventViz.RATIOSIZE
            elif self.sisize.isChecked():
                return EventViz.SISIZE
            else:
                return EventViz.SISIZE'''
            
    def __init__(self, fps=60, parent=None):
        QtGui.QWidget.__init__(self, parent)
        SelectiveConsumer.__init__(self, (("diff", ".*", "gestures"),), fps)
        """Records of sources' touch events."""
        self.__sources = {}
        """self.oldest = None
        self.__display = DisplayDevice.create()
        if self.__display.url.scheme=="dummy": 
            print("WARNING: using dummy DisplayDevice")
            self.__display.debug()
        self.drawmode = EventViz.SISIZE"""
        self.pointreduction = 1
        self.debuglevel = 0
        # Setup gui
        self.setWhatsThis("Event &Viz")
        self.sizehint = QtCore.QSize(320,240)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        """self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.connect(self, QtCore.SIGNAL("customContextMenuRequested(const QPoint &)"), self.__contextmenu)
        self.connect(QtGui.QShortcut('Alt+C', self), QtCore.SIGNAL("activated()"), self.__configpanel)"""
        self.connect(QtGui.QShortcut('Ctrl+Q', self), QtCore.SIGNAL("activated()"), self.close)
    
    '''
    def _addObservable(self, observable):
        Consumer._addObservable(self, observable)
        if not isinstance(observable, SourceList):
            self.__sources.setdefault(observable, {})
            # resize the widget if necessary
            gesturestate = observable.state.get("gestures", {})
            pos_si_range = gesturestate.get("pos_si_range")
            if pos_si_range and self.drawmode==EventViz.SISIZE:
                s = self.__display.mm2pixels([i*1000 for i in pos_si_range], trunc=True)
                self.sizehint = QtCore.QSize(max(s[0], self.width()), max(s[1], self.height()))
                self.window().adjustSize()
            self.update()'''

    def _removeObservable(self, observable):
        SelectiveConsumer._removeObservable(self, observable)
        self.__sources.pop(observable, None)
        self.update()

    def _consume(self, products, source):
        tracks = self.__sources.setdefault(source, {})
        diff = ExtensibleTree()
        for item in products:
            StateMachine.mergeDiff(diff, item.diff)
        for id_, node in diff.added.gestures.items():
            if "rel_pos" in node: 
                tracks[id_] = [node.rel_pos]
        for id_, node in diff.updated.gestures.items():
            if "rel_pos" in node:
                history = tracks.setdefault(id_, [])
                history.append(node.rel_pos)
        for id_, node in diff.removed.gestures.items():
            if "rel_pos" in node:
                tracks.pop(id_, None)
        self.update()
        """elif key=="timetag" and isinstance(value, datetime.datetime):
            if self.oldest is None or value<self.oldest:
            self.oldest = value"""

    def paintEvent(self, event):
        if self.debuglevel>3:
            timer = QtCore.QElapsedTimer()
            timer.start();
        count = 0
        width, height = self.width(), self.height()
        painter = QtGui.QPainter(self)        
        o = 4 # position circle size
        # Draw grid
        painter.setPen(QtGui.QColor(200,200,200))
        for i in range(0, 100, 10):
            x = i*width/100
            y = i*height/100
            painter.drawLine(0, y, width, y)
            painter.drawLine(x, 0, x, height)
        painter.setFont(QtGui.QFont( "courier", 9))
        for source, tracks in self.__sources.items():
            fill, outline = (#source.state.get("color",
                                             (QtCore.Qt.gray, QtCore.Qt.black))
            deviceratio = None
            """gesturestate = source.state.get("gestures", {})
            pos_si_range = gesturestate.get("pos_si_range")
            if pos_si_range is not None:
                deviceratio = float(pos_si_range[0])/pos_si_range[1] 
            else: deviceratio = None
            if pos_si_range and self.drawmode!=EventViz.WINSIZE:
                # Draw device area
                if self.drawmode==EventViz.SISIZE:
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
            # Draw tracks
            for evid, history in tracks.items():
                #gesture = gesturestate.get(evid, ExtensibleEvent())
                # Draw first point
                painter.setPen(outline)
                painter.setBrush(outline)
                pos0 = self.__tovizpos(history[0], deviceratio)
                painter.drawEllipse(pos0[0]-3, pos0[1]-3, 6, 6)
                # Draw path
                painter.setBrush(fill)
                posN = self.__tovizpos(history[-1], deviceratio)
                x, y = posN[0], posN[1] 
                if len(history)>1:
                    path = QtGui.QPainterPath()
                    path.moveTo(pos0[0], pos0[1]);
                    for e in history[1:-1:self.pointreduction]:
                        posI = self.__tovizpos(e, deviceratio)
                        path.lineTo(posI[0], posI[1])
                        count += 1
                    path.lineTo(x, y)
                    painter.strokePath(path, painter.pen())
                """
                # Draw boundingbox if defined                
                bb = gesture.get("boundingbox")
                if bb is not None:       
                    bb_rel_size = bb.getRel("size", 
                                            gesturestate.get("boundingbox"), 
                                            True)                    
                    if bb_rel_size is not None:
                        bb_angle = bb.getSI("angle",
                                            gesturestate.get("boundingbox"), 
                                            True)
                        bb_pos = self.__tovizpos(bb, deviceratio)
                        if bb_pos is not None: bb_x, bb_y = bb_pos 
                        else: bb_x, bb_y = x, y   
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
                objclass = gesture.get("objclass")
                if objclass is not None:
                    painter.save()
                    painter.setPen(QtCore.Qt.black)
                    painter.drawText(x+1.5*o, y-2*o, "obj: %d"%objclass)
                    painter.restore()
                # Draw orientation if defined
                angle = gesture.getSI("angle", gesturestate)
                if angle is not None:
                    painter.save()
                    pencolor = QtGui.QColor(fill)
                    pencolor.setAlphaF(0.85)
                    painter.setPen(QtGui.QPen(pencolor, 4))
                    l = 25
                    dx = math.cos(angle[0]) * l
                    dy = math.sin(angle[0]) * l
                    painter.drawLine(x, y, x+dx, y+dy)           
                    painter.restore()"""
                # Draw current position 
                painter.drawEllipse(x-o, y-o, o+o, o+o)
                # Print additional information
                """ if self.debuglevel>0:
                    painter.setPen(QtCore.Qt.black)
                    painter.drawText(x+1.5*o, y+o, "%s (%s)"%(evid, len(history)))
                    if self.debuglevel>1:
                        i = 1
                        rel_pos = history[-1].rel_pos
                        painter.drawText(x+1.5*o, y+o+i*10,
                                         "%.3f,%.3f (rel)"%(rel_pos[0], 
                                                            rel_pos[1]))
                        pos = gesture.get("pos")
                        if pos: 
                            i += 1 
                            painter.drawText(x+1.5*o, y+o+i*10,
                                             "%g,%g"%(pos[0], pos[1]))
                        si_pos = history[-1].get("si_pos")
                        if si_pos: 
                            i += 1
                            painter.drawText(x+1.5*o, y+o+i*10,
                                             "%.4f,%.4f (m)"%(si_pos[0], 
                                                              si_pos[1]))
                        if self.debuglevel>2:
                            i += 1
                            painter.drawText(x+1.5*o, y+o+i*10, 
                                             source.state.get("name","???"))
        if self.debuglevel>3:
            painter.setPen(QtCore.Qt.black)
            sum = 0
            for tracks in self.__sources.values(): sum = sum + len(tracks)
            painter.drawText(5,10,
                             "%d sources; %d tracks; %d points;  %d ms"\
                                 %(len(self.__sources), sum, count, timer.elapsed()))
            if self.oldest:
                lag = datetime.datetime.now()-self.oldest
                msecs = lag.seconds*1000+lag.microseconds/1000.
                painter.drawText(5, 20, "lag: %d msecs"%msecs)
        self.oldest = None"""
    '''
    def keyPressEvent(self, event):
        key = event.key()
        if key==QtCore.Qt.Key_Space:
            self.debuglevel = (self.debuglevel + 1) % 5
            self.update()
        else: QtGui.QWidget.keyPressEvent(self, event)'''
        
    def sizeHint(self):
        return self.sizehint

    def __tovizpos(self, event, deviceratio=None):
        """Return the coordinates in pixel for the specified event
        of None if it can't be determined."""
        rvalue = None
        """if self.drawmode==EventViz.SISIZE:
            rvalue = event.get("pixel_pos")
        elif self.drawmode==EventViz.RATIOSIZE and deviceratio is not None:
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
                rvalue = list(pos)
                rvalue[0] *= self.width()
                rvalue[1] *= self.height()
        return rvalue
    
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
        config = EventViz.ConfigPanel(self.drawmode)
        if config.exec_():
            self.drawmode = config.drawmode()
            self.update()'''
