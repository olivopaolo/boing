# -*- coding: utf-8 -*-
#
# boing/utils/StatProducer.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import datetime
import io
import weakref

from PyQt4 import QtCore

from boing.eventloop.MappingEconomy import MappingProducer
from boing.eventloop.OnDemandProduction import OnDemandProducer, SelectiveConsumer
from boing.utils.ExtensibleTree import ExtensibleTree

class StatProducer(SelectiveConsumer, MappingProducer):

    class StatRecord(object):
        def __init__(self):
            self.tot = 0
            self.partial = 0
            self.lagmax = None

    def __init__(self, requests=OnDemandProducer.ANY_PRODUCT, 
                 hz=1, inhz=None, parent=None):
        SelectiveConsumer.__init__(self, requests, hz=inhz)
        MappingProducer.__init__(self, productoffer={"data", "str"}, 
                                 parent=parent)
        self.__tid = QtCore.QTimer()
        self.__tid.timeout.connect(self.__produce)
        self.__tid.start(1000/hz)
        self.__stat = {}
        self._postdata = False
        self._poststr = False
        self.update = False

    def _removeObservable(self, observable):
        SelectiveConsumer._removeObservable(self, observable)
        for ref in self.__stat.keys():
            if ref() is observable: 
                del self.__sources[ref] ; break

    def _checkRef(self):
        SelectiveConsumer._checkRef(self)
        MappingProducer._checkRef(self)
        self.__stat = dict((k, v) for k, v in self.__stat.items() \
                                   if k() is not None)

    def _updateOverallDemand(self):
        MappingProducer._updateOverallDemand(self)
        self._postdata = self.matchDemand("data")
        self._poststr = self.matchDemand("str")

    def _consume(self, products, producer):
        self.update = True
        stat = None
        for ref, record in self.__stat.items():
            if ref() is producer: stat = record ; break
        else:
            stat = StatProducer.StatRecord()
            self.__stat[weakref.ref(producer)] = stat
        now = datetime.datetime.now()
        for p in products:
            stat.partial += 1
            if "timetag" in p and p["timetag"] is not None:
                delta = now - p["timetag"]
                if stat.lagmax is None or delta>stat.lagmax:
                    stat.lagmax = delta

    def __produce(self):
        if self.update:
            self.update = False
            data = io.StringIO()
            intro = False
            for ref, record in self.__stat.items():
                if record.partial>0:
                    if not intro: 
                        data.write("Production report: \n") ; intro = True
                    record.tot += record.partial
                    data.write(str(ref()))
                    data.write("\n")
                    if record.lagmax is not None:
                        msecs = record.lagmax.seconds*1000 \
                            +record.lagmax.microseconds/1000
                        record.lagmax = None
                        data.write("  tot=%d, hz=%g, lagmax=%f ms\n"%(
                                record.tot, 
                                record.partial*1000/self.__tid.interval(), 
                                msecs))
                    else:
                        data.write("  tot=%d, hz=%d\n"%(record.tot, record.partial))
                    record.partial = 0
            if intro: data.write("\n")
            if self._postdata or self._poststr:
                product = ExtensibleTree()
                if self._postdata: product.data = data.getvalue().encode() 
                if self._poststr: product.str = data.getvalue()
                self._postProduct(product)
