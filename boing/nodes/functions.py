# -*- coding: utf-8 -*-
#
# boing/nodes/functions.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.
'''
import collections
import copy
import datetime

from PyQt4 import QtCore, QtGui

from boing.core.MappingEconomy import Node, FunctionalNode
import boing.utils as utils
import boing.utils.QPath as QPath


class ArgumentFunction(FunctionalNode):
    """The node's function is set from a constructor parameter."""

    def __init__(self, function, *args, **kwargs):
        FunctionalNode.__init__(self, *args, **kwargs)
        if not isinstance(function, collections.Callable):
            raise TypeError("'%s' object is not callable"%type(function))
        self.__argfunction = function

    def _function(self, *args, **kwargs):
        self.__argfunction(*args, **kwargs)


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

'''
