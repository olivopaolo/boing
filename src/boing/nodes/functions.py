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
from boing.core.MappingEconomy import Node

class Filter(Node):
    """It forwards everything it requires."""
    def _consume(self, products, producer):
        for p in products:
            self._postProduct(p)


class FilterOut(Node):
    def __init__(self, filterout, request=OnDemandProducer.ANY_PRODUCT,             
                 hz=None, parent=None):
        #FIXME: set productoffer
        Node.__init__(self, request=request, hz=hz, parent=parent)
        self.filterout = QPath.QPath(filterout) \
            if filterout is not None and not isinstance(filterout, QPath.QPath) \
            else filterout

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

class BaseFunction(Node):

    def __init__(self, args, target=None, update=False, function=None,
                 request=OnDemandProducer.ANY_PRODUCT, hz=None, parent=None):
        #FIXME: set productoffer
        Node.__init__(self, request=request, hz=hz, parent=parent)
        self._functionobj = function
        self._args = QPath.QPath(args) \
            if args is not None and not isinstance(args, QPath.QPath) \
            else args
        self._target = target
        self._update = update

    def _consume(self, products, producer):
        for p in products:
            paths, args = self._args.items(p)
            if paths:
                forward = copy.deepcopy(p) if self._update else utils.quickdict()
                for path, value in zip(self._target(*paths) \
                                           if self._target is not None \
                                           else paths, 
                                       self._function(*args)):
                    split = path.split(";")
                    if len(split)==1: forward = value
                    else:
                        node = forward
                        for key in split[1:-1]: 
                            node = node[key]
                        node[split[-1]] = value
                self._postProduct(forward)
            elif self._update:
                self._postProduct(p)

    def _function(self, *args):
        if self._functionobj is not None: self._functionobj(*args)


class Calibration(BaseFunction):

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

    def __init__(self, matrix, args, target=None, update=True,
                 request=OnDemandProducer.ANY_PRODUCT, hz=None, parent=None):
        BaseFunction.__init__(self, args, target, update, 
                              request=request, hz=hz, parent=parent)
        self._matrix = matrix

    def _function(self, *args):
        for v in args:
            if len(v)==2:
                point = self._matrix*QtGui.QVector4D(v[0], v[1], 0, 1)
                yield (point.x(), point.y())
            elif len(v)==3:
                point = self._matrix*QtGui.QVector4D(v[0], v[1], v[2], 1)
                yield (point.x(), point.y(), point.z())
            elif len(v)==4:
                point = self._matrix*QtGui.QVector4D(*v)
                yield (point.x(), point.y(), point.z(), point.w())
