# -*- coding: utf-8 -*-
#
# boing/utils/testutils.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections

from PyQt4 import QtCore

from boing.eventloop.OnDemandProduction import OnDemandProducer
from boing.eventloop.MappingEconomy import HierarchicalProducer, Node

class RenameNode(Node):

    def __init__(self, request, rename, target=None,
                 productoffer=None, hz=None, parent=None):
        Node.__init__(self, productoffer, request=request, hz=hz, parent=parent)
        self.rename = rename
        self.target = target if target is not None else request

    def _consume(self, products, producer):
        for p in products:
            if isinstance(p, collections.Mapping) and self.target in p:                
                self._postProduct({self.rename: p[self.target]})


class Timer(HierarchicalProducer):

    def __init__(self, *args, **kwargs):
        # FIXME: set productoffer
        HierarchicalProducer.__init__(self, *args, **kwargs)
        self.__timer = QtCore.QTimer()
        self.__timer.timeout.connect(self.__timeout)

    def start(self, msec=None):
        self.__timer.start() if msec is None else self.__timer.start(msec)

    def stop(self):
        self.__timer.stop()

    def interval(self):
        return self.__timer.interval()

    def isActive(self):
        return self.__timer.isActive()

    def isSingleShot(self):
        return self.__timer.isSingleShot()

    def setInterval(self, msec):
        self.__timer.setInterval(msec)

    def setSingleShot(self, singleShot):
        self.__timer.setSingleShot(singleShot)

    def timerId(self):
        return self.__timer.timerId()

    @QtCore.pyqtSlot()
    def __timeout(self):
        self._postProduct({"timeout":None})

