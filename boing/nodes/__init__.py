# -*- coding: utf-8 -*-
#
# boing/nodes/__init__.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import datetime
import io
import weakref

from PyQt4 import QtCore

from boing.core import Offer, Request, Product, Functor
from boing.utils import assertIsInstance, deepDump

class Dump(Functor):

    def __init__(self, src=False, dest=False, depth=None, 
                 request=Request.ANY, parent=None):
        super().__init__(request, Offer(Product(str=str())), Functor.RESULTONLY, 
                         parent=parent)
        self.dumpsrc = assertIsInstance(src, bool)
        self.dumpdest = assertIsInstance(dest, bool)
        self.depth = None if depth is None else int(depth)

    def _process(self, sequence, producer):
        stream = io.StringIO()
        if self.dumpsrc: 
            stream.write("from: %s\n"%str(producer))
        if self.dumpdest: 
            stream.write("DumpNode(request=%s)\n"%repr(str(self.request())))
        for operands in sequence:
            deepDump(Product(operands), stream, self.depth)
            stream.write("\n")
        yield (("str", stream.getvalue()),)


class StatProducer(Functor):

    class _StatRecord(object):
        def __init__(self):
            self.tot = 0
            self.partial = 0
            self.tags = set()
            self.lagmax = None

    def __init__(self, request=Request.ANY, fps=1, **kwargs):
        super().__init__(request, Offer(str=Product(str=str())), **kwargs)
        self.__timer = QtCore.QTimer(timeout=self.__produce)        
        self.__timer.start(1000/float(fps))
        self._inittime = datetime.datetime.now()
        self.__stat = {}
        self._update = False

    def _checkRefs(self):
        super()._checkRefs()
        f = lambda kw: kw[0]() is not None
        self.__stat = dict(filter(f, self.__stat.items()))

    def _removeObservable(self, observable):
        super()._removeObservable(observable)
        for ref in self.__stat.keys():
            if ref() is observable: 
                del self.__sources[ref] ; break

    def _consume(self, products, producer):
        self._update = True
        # Get producer record
        record = None
        for ref, rec in self.__stat.items():
            if ref() is producer: record = rec ; break
        else:
            record = StatProducer._StatRecord()
            self.__stat[weakref.ref(producer)] = record
        # Update record
        now = datetime.datetime.now()
        for p in products:
            record.partial += 1
            record.tags.update(p.keys())
            if "timetag" in p:
                timetag = p["timetag"]
                if timetag is not None:
                    delta = now - timetag
                    if record.lagmax is None or delta>record.lagmax:
                        record.lagmax = delta

    def __produce(self):
        if self._update and self.isRequested(tag="str"):
            self._update = False
            data = io.StringIO()
            intro = False
            for ref, record in self.__stat.items():
                if record.partial>0:
                    if not intro:
                        delta = datetime.datetime.now() - self._inittime
                        data.write("Statistics after %s\n"%delta)
                        intro = True
                    record.tot += record.partial
                    data.write(str(ref()))
                    data.write("\n")
                    data.write("  tags: %s\n"%record.tags)
                    if record.lagmax is not None:
                        msecs = record.lagmax.seconds*1000 \
                            +record.lagmax.microseconds/1000
                        record.lagmax = None
                        data.write("  tot=%d, hz=%g, lagmax=%f ms\n"%(
                                record.tot, 
                                record.partial*1000/self.__timer.interval(), 
                                msecs))
                    else:
                        data.write("  tot=%d, hz=%d\n"%(record.tot, record.partial))
                    record.partial = 0
                    record.tags.clear()
            if intro: data.write("\n")
            self.postProduct(Product(str=data.getvalue()))


'''class Filter(economy.TransparentNode):
    def __init__(self, query, **kwargs):
        super().__init__(**kwargs)
        self.__query = assertIsInstance(query, economy.AdvancedRequest)

    def query(self):
        return self.__query

    def setQuery(self, query):
        self.__query = assertIsInstance(query, economy.AdvancedRequest)

    def _consume(self, products, producer):
        for product in products:
            subset = self.__query.filter(product)
            if subset: self.postProduct(subset)
'''
'''
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
'''
