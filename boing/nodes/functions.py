# -*- coding: utf-8 -*-
#
# boing/nodes/functions.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import copy
import datetime

from PyQt4 import QtCore, QtGui

from boing.core.MappingEconomy import Node, FunctionalNode
import boing.utils as utils


class ArgumentFunction(FunctionalNode):
    """The node function is set from a constructor parameter."""

    def __init__(self, function, *args, **kwargs):
        FunctionalNode.__init__(self, *args, **kwargs)
        if not isinstance(function, collections.Callable):
            raise TypeError("'%s' object is not callable"%type(function))
        self.__argfunction = function

    def _function(self, *args, **kwargs):
        self.__argfunction(*args, **kwargs)


class Filter(Node):
    """Filters the received products using a QPath query and it posts
    the results."""
    def __init__(self, query, request=Node.TRANSPARENT, hz=None, parent=None):
        super().__init__(request=request, hz=hz, parent=parent)
        self.__query = query \
            if query is None or isinstance(query, QPath.QPath) \
            else QPath.QPath(query)        

    def query(self):
        return self.__query

    def setQuery(self, query):
        self.__query = query \
            if query is None or isinstance(query, QPath.QPath) \
            else QPath.QPath(query)        

    def _consume(self, products, producer):
        for product in products:
            subset = self.__query.filter(product, deepcopy=False) \
                if self.__query is not None else None
            if subset: self._postProduct(subset)

# -------------------------------------------------------------------

class Lag(Node):
    """Add a lag to the product pipeline."""
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
    """Add to each product the timestamp at the time the product is
    received as the item with keyword "timetag".""" 
    def __init__(self, hz=None, parent=None):
        super().__init__(None, "timetag", {"timetag": datetime.datetime.now()},
                         request=Node.TRANSPARENT, hz=hz, parent=parent)
  
    def _function(self, paths, values):
        yield datetime.datetime.now()

# -------------------------------------------------------------------

class ArgumentFunctor(FunctionalNode):
    """It takes a functorfactory and for each different argument path,
    it creates a new functor which is applied to the argument
    value. After a functor is created, it is stocked and it is never
    dropped."""
    def __init__(self, functorfactory, *args, **kwargs):
        FunctionalNode.__init__(self, *args, **kwargs)
        self.__factory = functorfactory
        self.__functors = utils.quickdict()
    
    def _function(self, paths, values):
        for key, value in zip(paths, values):
            item = self.__functors
            split = key.split(".")
            for step in split[:-1]:
                item = item[step]
            if isinstance(value, collections.Sequence):
                functor = item.setdefault(
                    split[-1], 
                    tuple(self.__factory.create() for i in range(len(value))))
                if hasattr(value, "__setitem__") \
                        and self._resultmode==FunctionalNode.MERGE:
                    for i, item in enumerate(value):
                        value[i] = type(item)(functor[i](item))
                else:
                    value = type(value)((type(item)(functor[i](item)) \
                                             for i,item in enumerate(value)))
                yield value
            elif isinstance(value, collections.Mapping):
                raise NotImplementedError()
            else:
                functor = item.setdefault(split[-1], self.__factory.create())
                yield type(value)(functor(value))

                
class DiffArgumentFunctor(FunctionalNode):
    """It takes a functorfactory and for each different argument path,
    it creates a new functor which is applied to the argument
    value. The args must be a diff-based path so that functor can be
    removed depending on 'diff.removed' instances."""
    def __init__(self, functorfactory, *args, **kwargs):
        FunctionalNode.__init__(self, *args, **kwargs)
        self.__factory = functorfactory
        self.__functors = utils.quickdict()

    def _function(self, paths, values):
        for key, value in zip(paths, values):
            # key is supposed to be a string like:
            #   diff.<action>.<path...>.<attribute>
            split = key.split(".")
            action = split[1]
            if action in ("added", "updated"):
                item = self.__functors
                for step in split[2:-1]:
                    item = item[step]
                if isinstance(value, collections.Sequence):
                    functor = item.setdefault(
                        split[-1], 
                        tuple(self.__factory.create() \
                                  for i in range(len(value))))
                    if hasattr(value, "__setitem__") \
                            and self._resultmode==FunctionalNode.MERGE:
                        for i, item in enumerate(value):
                            value[i] = type(item)(functor[i](item))
                    else:
                        value = type(value)((type(item)(functor[i](item)) \
                                                 for i,item in enumerate(value)))
                    yield value
                elif isinstance(value, collections.Mapping):
                    raise NotImplementedError()
                else:
                    functor = item.setdefault(split[-1], self.__factory.create())
                    yield type(value)(functor(value))
            elif action=="removed":                
                split = key.split(".")
                item = self.__functors
                for step in split[2:]:
                    item = item[step]
                for k in value.keys():
                    item.pop(k, None)
                yield value
            else:
                raise ValueError("Unexpected action: %s", action)

# -------------------------------------------------------------------

class Calibration(FunctionalNode):
    """Apply a 4x4 transformation matrix to each target value."""

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
        for value in values:
            if len(value)==2:
                point = self._matrix*QtGui.QVector4D(value[0], value[1], 0, 1)
                yield [point.x(), point.y()]
            elif len(value)==3:
                point = self._matrix*QtGui.QVector4D(value[0], value[1], value[2], 1)
                yield [point.x(), point.y(), point.z()]
            elif len(value)==4:
                point = self._matrix*QtGui.QVector4D(*value)
                yield [point.x(), point.y(), point.z(), point.w()]

