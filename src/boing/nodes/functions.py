# -*- coding: utf-8 -*-
#
# boing/multitouch/functions.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import datetime

from PyQt4 import QtCore, QtGui

from boing.core.MappingEconomy import Node, FunctionalNode


class Lag(Node):

    def __init__(self, msec, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lag = msec
        self.__buffer = collections.deque()

    def __timeout(self):
        self._postProduct(self.__buffer.popleft())
        
    def _consume(self, products, producer):
        for p in products:
            self.__buffer.append(p)
            QtCore.QTimer.singleShot(self.lag, self.__timeout)


class Timekeeper(FunctionalNode):
    
    def __init__(self, hz=None, parent=None):
        super().__init__(None, "timetag", {"timetag": datetime.datetime.now()},
                         request=Node.TRANSPARENT, hz=hz, parent=parent)
  
    def _function(self, paths, values):
        yield datetime.datetime.now()


# -------------------------------------------------------------------

class ArgumentFunction(FunctionalNode):

    def __init__(self, function, *args, **kwargs):
        FunctionalNode.__init__(self, *args, **kwargs)
        self.__argfunction = function

    def _function(self, *args, **kwargs):
        self.__argfunction(*args, **kwargs)


class Calibration(FunctionalNode):

    Identity = QtGui.QMatrix4x4()
    Right = QtGui.QMatrix4x4(0.0,-1.0, 0.0, 1.0, 
                             1.0, 0.0, 0.0, 0.0, 
                             0.0, 0.0, 1.0, 0.0,
                             0.0, 0.0, 0.0, 1.0)
    Inverted = QtGui.QMatrix4x4(-1.0, 0.0, 0.0, 1.0, 
                                 0.0,-1.0, 0.0, 1.0, 
                                 0.0, 0.0, 1.0, 0.0,
                                 0.0, 0.0, 0.0, 1.0)
    Left = QtGui.QMatrix4x4( 0.0, 1.0, 0.0, 0.0, 
                            -1.0, 0.0, 0.0, 1.0, 
                             0.0, 0.0, 1.0, 0.0,
                             0.0, 0.0, 0.0, 1.0)

    def __init__(self, matrix, *args, **kwargs):
        FunctionalNode.__init__(self, *args, **kwargs)
        self._matrix = matrix

    def _function(self, paths, values):
        for v in values:
            if len(v)==2:
                point = self._matrix*QtGui.QVector4D(v[0], v[1], 0, 1)
                yield (point.x(), point.y())
            elif len(v)==3:
                point = self._matrix*QtGui.QVector4D(v[0], v[1], v[2], 1)
                yield (point.x(), point.y(), point.z())
            elif len(v)==4:
                point = self._matrix*QtGui.QVector4D(*v)
                yield (point.x(), point.y(), point.z(), point.w())
