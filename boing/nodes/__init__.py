# -*- coding: utf-8 -*-
#
# boing/nodes/__init__.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import datetime
import io
import weakref

from PyQt4 import QtCore

from boing import \
    Offer, Request, Product, Producer, Consumer, Functor, Identity
from boing.core.graph import SimpleGrapher
from boing.utils import assertIsInstance, deepDump, quickdict

# -------------------------------------------------------------------
# Dump

class Dump(Functor, Consumer.CONFIGURABLE):

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

# -------------------------------------------------------------------
# StatProducer

class StatProducer(Functor, Consumer.CONFIGURABLE):

    class _StatRecord(object):
        def __init__(self):
            self.tot = 0
            self.partial = 0
            self.tags = set()
            self.lagmax = None

    def __init__(self, request=Request.ANY, fps=1, parent=None):
        super().__init__(request, Offer(Product(str=str())), Functor.RESULTONLY, 
                         parent=parent)
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
        if self._update:
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

# -------------------------------------------------------------------
# SimpleGrapherProducer

class SimpleGrapherProducer(Producer):
    
    _SEPARATOR = """

================================================================================

"""
    def __init__(self, starters=tuple(), request=Request.ANY, maxdepth=None,
                 hz=1, parent=None):
        super().__init__(Offer(Product(str=str())), parent=parent)
        self._starters = starters
        self._grapher = SimpleGrapher(request)
        self.__tid = QtCore.QTimer(timeout=self._draw)
        if hz: self.__tid.start(1000/hz)
        if hz<1: QtCore.QTimer.singleShot(100, self._draw)
        self.maxdepth = maxdepth
        self.separator = SimpleGrapherProducer._SEPARATOR

    def starters(self):
        return self._starters

    def setStarters(self, starters):
        self._starters = starters

    def _draw(self):
        stream = io.StringIO()
        memo = set()
        for node in self._starters:
            self._grapher.draw(node, stream, maxdepth=self.maxdepth, memo=memo)
        graph = stream.getvalue()
        if graph: self.postProduct(Product(str=self.separator+graph))

# -------------------------------------------------------------------

class Lag(Identity):
    """Add a lag to the product pipeline."""
    def __init__(self, msec, parent=None):
        super().__init__(parent=parent)
        self.lag = msec
        self.__buffer = collections.deque()

    def __timeout(self):
        self.postProduct(self.__buffer.popleft())
        
    def _consume(self, products, producer):
        for p in products:
            self.__buffer.append(p)
            QtCore.QTimer.singleShot(self.lag, self.__timeout)

# -------------------------------------------------------------------

class Timekeeper(Functor):
    """Add to each product the timestamp at the time the product is
    received as the item with keyword "timetag".""" 
    def __init__(self, parent=None):
        super().__init__(Request.NONE, 
                         Offer(Product(timetag=datetime.datetime.now())),
                         blender=Functor.MERGECOPY, parent=parent)
  
    def _process(self, sequence, producer):
        for operands in sequence:
            yield (("timetag", datetime.datetime.now()), )

# -------------------------------------------------------------------

class Editor(Functor):

    def __init__(self, dict, blender, parent=None):
        super().__init__(Request.NONE, Offer(Product(**dict)), blender, 
                         parent=parent)
        self.__dict = dict

    def items(self):
        return self.__dict.items()

    def get(self, key, default=None):
        return self.__dict.get(key, default)

    def set(self, key, value):
        self.__dict[key] = value

    def _process(self, sequence, producer):
        for operands in sequence:
            yield tuple(self.items())

# -------------------------------------------------------------------

class Filter(Identity):
    def __init__(self, query, parent=None):
        super().__init__(parent=parent)
        self.__query = assertIsInstance(query, Request)

    def query(self):
        return self.__query

    def setQuery(self, query):
        self.__query = assertIsInstance(query, Request)

    def _consume(self, products, producer):
        for product in products:
            subset = self.__query.filter(product)
            if subset: self.postProduct(subset)

    def _propagateOffer(self):
        if self._consumer() is not None:
            if self.isPropagatingOffer():
                offers = (obs.offer() for obs in self._consumer().observed() \
                              if isinstance(obs, Producer))
                updated = self._selfOffer()
                for offer in offers:
                    updated += Offer(self.query().filter(offer))
            else:
                update = self._selfOffer()
            if self.offer()!=updated:
                self._cumulatedoffer = updated
                self.offerChanged.emit()

# -------------------------------------------------------------------

class DiffArgumentFunctor(Functor):
    """It takes a functorfactory and for each different argument path,
    it creates a new functor which is applied to the argument
    value. The args must be a diff-based path so that functor can be
    removed depending on 'diff.removed' instances."""
    def __init__(self, functorfactory, 
                 request, blender, parent=None):
        super().__init__(request, Functor.TUNNELING, blender, parent=parent)
        self.__factory = functorfactory
        self.__functors = quickdict()

    def _process(self, sequence, producer):
        for operands in sequence:
            yield tuple(self._applyFunctor(operands))

    def _applyFunctor(self, operands):
        for key, value in operands:
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
                            and isinstance(self.blender, Functor.MergeBlender):
                        for i, item in enumerate(value):
                            value[i] = type(item)(functor[i](item))
                    else:
                        value = type(value)((type(item)(functor[i](item)) \
                                                 for i,item in enumerate(value)))
                    yield (key, value)
                elif isinstance(value, collections.Mapping):
                    raise NotImplementedError()
                else:
                    functor = item.setdefault(split[-1], self.__factory.create())
                    yield (key, type(value)(functor(value)))
            elif action=="removed":                
                split = key.split(".")
                item = self.__functors
                for step in split[2:]:
                    item = item[step]
                for k in value.keys():
                    item.pop(k, None)
            else:
                raise ValueError("Unexpected action: %s", action)

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
