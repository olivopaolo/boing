# -*- coding: utf-8 -*-
#
# boing/multitouch/functions.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import copy
import collections
import datetime
import weakref

from PyQt4 import QtCore, QtGui

import boing.utils.QPath as QPath
import boing.utils as utils
from boing.core.OnDemandProduction import OnDemandProducer
from boing.core.MappingEconomy import Node, FunctionalNode

class Filter(Node):
    """It forwards everything it requires."""
    def _consume(self, products, producer):
        for p in products:
            self._postProduct(p)


class FilterOut(Node):
    def __init__(self, out=OnDemandProducer.ANY_PRODUCT, 
                 request=OnDemandProducer.ANY_PRODUCT,             
                 hz=None, parent=None):
        #FIXME: set productoffer
        Node.__init__(self, request=request, hz=hz, parent=parent)
        self.filterout = QPath.QPath(out) \
            if out is not None and not isinstance(out, QPath.QPath) \
            else out

    def filterOut(self):
        return self._filterout

    def setFilterOut(self, filterout):
        self.filterout = QPath.QPath(request) \
            if filterout is not None and not isinstance(request, QPath.QPath) \
            else filterout
    
    """It forwards everything it requires."""
    def _consume(self, products, producer):
        for p in products:
            filtered = FilterOut.filterout(p, self.filterout)
            self._postProduct(filtered)
            
    @staticmethod
    def filterout(product, filterout):
        """Return the subset of 'product' that matches 'request' or
        None."""
        if filterout==OnDemandProducer.ANY_PRODUCT:
            rvalue = Node
        elif filterout is None:
            rvalue = product
        else:
            rvalue = filterout.filterout(product)
        return rvalue


class Lag(Node):

    def __init__(self, msec, *args, **kwargs):
        Node.__init__(self, *args, **kwargs)
        self.lag = msec
        self.__buffer = collections.deque()

    def __timeout(self):
        self._postProduct(self.__buffer.popleft())
        
    def _consume(self, products, producer):
        for p in products:
            self.__buffer.append(p)
            QtCore.QTimer.singleShot(self.lag, self.__timeout)

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
