# -*- coding: utf-8 -*-
#
# boing/extra/pydoc.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import io

import pydot
from PyQt4 import QtCore

from boing.core import Request
from boing.core.graph import Grapher
from boing.utils import assertIsInstance, deepDump

class DotGrapher(Grapher):

    def __init__(self, request=Request.ANY):
        self.request = assertIsInstance(request, Request)

    def _drawPrologue(self, node, file, level):
        pass

    def _drawNode(self, node, file, level):
        stream = io.StringIO()
        print("%s: "%(node.__class__.__name__), end="", file=stream)
        data = self.request.filter(node._debugData())
        deepDump(data, stream, indent=2, end="\l", sort=False)
        print(end="\l", file=stream)
        file.add_node(pydot.Node(self._ref(self._getId(node)),
                                 label=stream.getvalue(), 
                                 shape="box"))

    def _drawSiblings(self, node, file, level, maxdepth, memo):
        for key, siblings in node._debugSiblings().items():
            if isinstance(siblings, collections.Iterable):
                for item in siblings:
                    self.draw(item, file, level+1, maxdepth, memo)
                    edge = pydot.Edge(self._ref(self._getId(node)),
                                      self._ref(self._getId(item)))
                    file.add_edge(edge)

            else:
                self.draw(siblings, file, level+1, maxdepth, memo)
                edge = pydot.Edge(self._ref(self._getId(node)),
                                  self._ref(self._getId(siblings)))
                file.add_edge(edge)
                    
    def _drawEpilogue(self, node, file, level):
        pass

    def _drawRef(self, key, file, level):
        pass

    def _ref(self, key):
        return "%s"%key


class DotGrapherProducer():

    def __init__(self, starters=tuple(), request=Request.ANY, maxdepth=None,
                 hz=0.1, parent=None):
        self._starters = starters
        self._grapher = DotGrapher(request)
        self.__tid = QtCore.QTimer(timeout=self._draw)
        if hz: self.__tid.start(1000/hz)
        if hz<1: QtCore.QTimer.singleShot(100, self._draw)
        self.maxdepth = maxdepth

    def starters(self):
        return self._starters

    def setStarters(self, starters):
        self._starters = starters

    def _draw(self):
        graph = pydot.Dot(graph_type='graph', labelalign="l")
        memo = set()
        for node in self._starters:
            self._grapher.draw(node, graph, maxdepth=self.maxdepth, memo=memo)
        graph.write_ps('/tmp/boing.ps')
