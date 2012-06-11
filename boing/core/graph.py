# -*- coding: utf-8 -*-
#
# boing/core/graph.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

"""The graph module provides the base classes for creating graphs and
few abstract classes for traversing and drawing a graph.

"""

import abc
import collections
import sys
import weakref

from boing.core.economy import Request
from boing.utils import assertIsInstance


class Node:

    _records = dict()

    _counter = 0

    def __init__(self):
        self.__id = Node._nextId(self)

    def __del__(self):
        Node._checkRecords()
    
    # Identifiable
    def id(self):
        return self.__id

    @staticmethod
    def _checkRecords():
        f = lambda kw: kw[1]() is not None
        Node._records = dict(filter(f, Node._records.items()))

    @staticmethod
    def get(id):
        return Node._records[id]()

    @staticmethod
    def _nextId(node):        
        Node._counter += 1
        rvalue = Node._counter
        Node._records[rvalue] = weakref.ref(node)
        return rvalue

    # Debuggable
    def debug(self, fd=sys.stdout, maxdepth=1, grapher=None):
        if grapher is None: grapher = SimpleGrapher() 
        grapher.draw(self, file=fd, maxdepth=maxdepth, memo=set())

    def _debugData(self): return collections.OrderedDict(id=self.id())

    def _debugSiblings(self): return collections.OrderedDict()

# -------------------------------------------------------------------
# GraphDrawers

class Grapher(metaclass=abc.ABCMeta):
    """FIXME: Very bad design."""
    def draw(self, node, file, level=0, maxdepth=None, memo=None):
        key = self._getId(node)
        if memo is None or key not in memo:
            if memo is not None: memo.add(key)
            self._drawNode(node, file, level)
            self._drawSiblings(node, file, level, maxdepth, memo)
        else:
            self._drawRef(key, file, level)

    @abc.abstractmethod
    def _drawNode(self, node, file, level): pass

    @abc.abstractmethod
    def _drawSiblings(self, node, file, level, maxdepth): pass

    @abc.abstractmethod
    def _ref(self, key): pass

    def _getId(self, node): return node.id() if hasattr(node, "id") else id(node)


class SimpleGrapher(Grapher):

    INDENT = 6

    def __init__(self, request=Request.ANY):
        self.request = assertIsInstance(request, Request)

    def _drawNode(self, node, file, level):
        b = SimpleGrapher.getIndent(level)
        print(b+"%s: {"%(node.__class__.__name__), file=file)
        data = self.request.filter(node._debugData())
        if data:
            for key, value in data.items():
                print(b+"  %s: %s,"%(str(key), str(value)), file=file)

    def _drawSiblings(self, node, file, level, maxdepth, memo):
        b = SimpleGrapher.getIndent(level)
        for key, siblings in node._debugSiblings().items():
            if isinstance(siblings, collections.Iterable):
                print(b+"  %s: ["%key, end="", file=file)
                if not siblings:
                    print("],", file=file)
                elif maxdepth is None or level<maxdepth:
                    if memo is not None \
                            and all(map(lambda node: self._getId(node) in memo, 
                                        siblings)):
                        print("%s],"%", ".join(self._ref(self._getId(s)) \
                                                   for s in siblings),
                              file=file)
                    else:
                        print("", file=file)
                        for item in siblings:
                            print("", file=file)
                            self.draw(item, file, level+1, maxdepth, memo)
                        print(b+"  ],", file=file)
                else:
                    print("...],", file=file)
            else:
                print(b+"  %s: "%key, end="", file=file)
                if siblings is None:
                    print("None,", file=file)
                elif maxdepth is None or level<maxdepth:
                    if memo is not None and self._getId(siblings) in memo:
                        print("%s,"%self._ref(self._getId(siblings)), file=file)
                    else:
                        print("\\", file=file)
                        self.draw(siblings, file, level+1, maxdepth, memo)
                        print("", file=file)
                else:
                    print("...,", file=file)
        print(b+"}", file=file)

    def _drawRef(self, key, file, level):
        pass

    def _ref(self, key):
        return "#%s"%key

    @staticmethod
    def getIndent(level):
        return " "*(level*SimpleGrapher.INDENT)
