# -*- coding: utf-8 -*-
#
# boing/nodes/__init__.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

"""The module :mod:`boing.nodes` contains a set of generic utility nodes.

"""

import collections
import datetime
import io
import logging
import weakref

from PyQt4 import QtCore

from boing.core import \
    Offer, Request, QRequest, Producer, Consumer, \
    WiseWorker, BaseWorker, Functor
from boing.core.graph import SimpleGrapher
from boing.net import Encoder as BaseEncoder
from boing.net import Decoder as BaseDecoder
from boing.utils import assertIsInstance, deepDump, quickdict

# -------------------------------------------------------------------
# Input/Output

class DataReader(Producer):

    def __init__(self, inputdevice, postend=True, parent=None):
        """:class:`Producer <boing.core.Producer>` node that anytime
        the device *inputdevice* send the signal :attr:`readyRead
        <boing.utils.fileutils.CommunicationDevice.readyRead>` it
        reads the device and it produces a message containing the
        data. The provided products is a dictionary ``{"str": data}``
        if ``data`` is a string, otherwise the product will be a
        dictionary like ``{"data": data}``.  If the argument *postend*
        is set to ``True``, the :class:`DataReader` will never produce
        an empty product, like ``{"str": ""}`` or ``{"data":
        b""}``. *parent* defines the parent of the node.

        """
        self._textmode = inputdevice.isTextModeEnabled()
        if self._textmode:
            offer = Offer(quickdict(str=str()))
            tags = dict(str=QRequest("str"))
        else:
            offer = Offer(quickdict(data=bytearray()))
            tags = dict(data=QRequest("data"))
        super().__init__(offer, tags=tags, parent=parent)
        self.__input = inputdevice
        self.__input.readyRead.connect(self._postData)
        self.postend = assertIsInstance(postend, bool)

    @QtCore.pyqtSlot()
    def _postData(self):
        data = self.__input.read()
        attr = "str" if self._textmode else "data"
        if attr in self._activetags and (data or self.postend):
            product = quickdict()
            product[attr] = data
            self.postProduct(product)

    def inputDevice(self):
        """Return the considered input device."""
        return self.__input


class DataWriter(Consumer):

    def __init__(self, outputdevice, writeend=True, hz=None, parent=None):
        """:class:`Consumer <boing.core.Consumer>` node that anytime
        it receives some data, it writes the data to the device
        *outputdevice*. The :class:`DataWriter` requires the products
        ``str`` if the output device is text enabled (see method
        :meth:`isTextModeEnabled
        <boing.utils.fileutils.IODevice.isTextModeEnabled>`) otherwise
        it requires the product ``data``. If the argument *writeend*
        is set to ``True``, the :class:`DataWriter` will never write
        an empty string; this can be useful in order to prevent a
        socket to close. *parent* defines the parent of the node.

        """
        self._textmode = outputdevice.isTextModeEnabled()
        super().__init__(request=QRequest("str" if self._textmode else "data"),
                         hz=hz, parent=parent)
        self.__output = outputdevice
        self.writeend = assertIsInstance(writeend, bool)

    def _consume(self, products, producer):
        flush = False
        attr = "str" if self._textmode else "data"
        for product in products:
            if attr in product:
                value = product[attr]
                if value or self.writeend:
                    self.__output.write(value) ; flush = True
        if flush: self.__output.flush()

    def outputDevice(self):
        """Return the considered output device."""
        return self.__output

'''class DataIO(DataReader, _BaseDataWriter):

    def __init__(self, inputdevice, outputdevice, hz=None, parent=None):
        DataReader.__init__(self, inputdevice, parent)
        _BaseDataWriter.__init__(self, outputdevice, hz)

    def __del__(self):
        DataReader.__del__(self)
        _BaseDataWriter.__del__(self)

    def _checkRefs(self):
        DataReader._checkRefs(self)
        _BaseDataWriter._checkRefs(self)'''

# -------------------------------------------------------------------
# Dump

class Dump(Functor, Functor.ConfigurableRequest):
    r"""Instances of the :class:`Dump` class produce a string
    representation of the products they receive. The string is
    obtained using the function :func:`boing.utils.deepDump`.

    The parameter *request* must be an instance of the class
    :class:`boing.core.Request` and it is used to select the product
    to be dumped. The default value for request is
    :attr:`Request.ALL<boing.core.Request.ALL>`. *mode* defines how the received
    products will be dumped. The available values are:

    * ``'keys'``, only the matched keys are written;
    * ``'values'``, only the values of the matched keys are written;
    * ``'items'``, both the keys and values are written.

    *separator* defines the string to be written between two
    products. The default value for separator is ``'\n\n'``. *src*
    defines whether the node also dumps the producer of the received
    products. The default for src is False. The paramenter *dest*
    defines whether the node adds a reference to itself when it dumps
    the received products; its default value is False. The parameter
    *depth* defines how many levels of the data hierarchy are explored
    and it is directly passed to the :func:`boing.utils.deepDump`
    function.

    """
    def __init__(self, request=Request.ANY, mode="items", separator="\n",
                 src=False, dest=False, depth=None, parent=None):
        super().__init__(request, Offer(quickdict(str=str())), Functor.RESULTONLY,
                         parent=parent)
        self.dumpsrc = assertIsInstance(src, bool)
        self.dumpdest = assertIsInstance(dest, bool)
        self.depth = None if depth is None else int(depth)
        if mode not in ("items", "values", "keys"): raise ValueError(
            "mode must be 'items' or 'values' or 'keys', not '%s'"%mode)
        else:
            self._mode = mode
        self.separator = assertIsInstance(separator, str, None)
        if self.separator is None: self.separator = ""

    def mode(self):
        """Return the node's mode."""
        return self._mode

    def setMode(self, mode):
        """Set the node's dump *mode*."""
        if mode not in ("items", "values", "keys"): raise ValueError(
            "mode must be 'items' or 'values' or 'keys', not '%s'"%mode)
        else:
            self._mode = mode

    def _process(self, sequence, producer):
        stream = io.StringIO()
        if self.dumpsrc:
            stream.write("from: %s\n"%str(producer))
        if self.dumpdest:
            stream.write("DumpNode(request=%s)\n"%repr(str(self.request())))
        for operands in sequence:
            data = quickdict(operands)
            if self.mode()=="items":
                deepDump(data, stream, self.depth)
                stream.write(self.separator)
            elif self.mode()=="values":
                values = tuple(data.values())
                deepDump(values if len(values)>1 else values[0],
                         stream, self.depth)
                stream.write(self.separator)
            elif self.mode()=="keys":
                deepDump(tuple(data.keys()), stream, self.depth)
                stream.write(self.separator)
        yield (("str", stream.getvalue()),)

# -------------------------------------------------------------------
# StatProducer

class StatProducer(Functor, Functor.ConfigurableRequest):

    class _StatRecord(object):
        def __init__(self):
            self.tot = 0
            self.partial = 0
            self.tags = set()
            self.lagmax = None

    def __init__(self, request=Request.ANY, fps=1, parent=None):
        super().__init__(request, Offer(quickdict(str=str())), Functor.RESULTONLY,
                         parent=parent)
        self.__timer = QtCore.QTimer(timeout=self.__produce)
        self.__timer.start(1000/float(fps))
        self._inittime = datetime.datetime.now()
        self.__stat = {}
        self._update = False
        self.observableRemoved.connect(self.__removeRecord)

    def _checkRefs(self):
        super()._checkRefs()
        f = lambda kw: kw[0]() is not None
        self.__stat = dict(filter(f, self.__stat.items()))

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

    def __removeRecord(self, observable):
        for ref in self.__stat.keys():
            if ref() is observable:
                del self.__sources[ref] ; break

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
            self.postProduct(quickdict(str=data.getvalue()))

# -------------------------------------------------------------------
# SimpleGrapherProducer

class SimpleGrapherProducer(Producer):

    _SEPARATOR = """

================================================================================

"""
    def __init__(self, starters=tuple(), request=Request.ANY, maxdepth=None,
                 hz=1, parent=None):
        super().__init__(Offer(quickdict(str=str())), parent=parent)
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
        if graph: self.postProduct(quickdict(str=self.separator+graph))

# -------------------------------------------------------------------

class Lag(BaseWorker):
    """Instances of the :class:`Lag` class forward the received
    products after a delay.

    The parameter *msec* defines the lag in milliseconds. *parent*
    must be a :class:`PyQt4.QtCore.QObject` and it defines the node's
    parent.

    """
    def __init__(self, msec, parent=None):
        super().__init__(request=Request.NONE, offer=Offer(), parent=parent)
        self.lag = msec
        self.__buffer = collections.deque()

    def __timeout(self):
        """Pop a product an forward it."""
        self.postProduct(self.__buffer.popleft())

    def _consume(self, products, producer):
        """For each received product, add it to the buffer and start a
        new timer."""
        for p in products:
            self.__buffer.append(p)
            QtCore.QTimer.singleShot(self.lag, self.__timeout)

# -------------------------------------------------------------------

class Timekeeper(Functor):
    """Instances of the :class:`Timekeeper` class tag each received
    product with the timestamp when the product is
    received; then they forward the product.

    *blender* defines the output of the node (see
    :class:`boing.core.Functor`). *parent* must be a
    :class:`PyQt4.QtCore.QObject` and it defines the node's parent.
    """
    def __init__(self, blender=Functor.MERGECOPY, parent=None):
        super().__init__(Request.NONE,
                         Offer(quickdict(timetag=datetime.datetime.now())),
                         blender, parent=parent)

    def _process(self, sequence, producer):
        for operands in sequence:
            yield (("timetag", datetime.datetime.now()), )

# -------------------------------------------------------------------

class Editor(Functor):
    """Instances of the :class:`Editor` class apply to the received
    products the (key, values) pairs of *dict*.

    *blender* defines the output of the node (see
    :class:`boing.core.Functor`). *parent* must be a
    :class:`PyQt4.QtCore.QObject` and it defines the node's parent.
    """
    def __init__(self, dict, blender, parent=None):
        super().__init__(Request.NONE, Offer(quickdict(**dict)), blender,
                         parent=parent)
        self.__dict = dict

    def items(self):
        """Return a new view of the editor dictionary's items ((key,
        value) pairs)."""
        return self.__dict.items()

    def get(self, key, default=None):
        """Return the value for *key* if *key* is in the editor's
        dictionary, else *default*. If *default* is not given, it
        defaults to None."""
        return self.__dict.get(key, default)

    def set(self, key, value):
        """Set the value for *key* to *value*."""
        self.__dict[key] = value

    def _process(self, sequence, producer):
        for operands in sequence:
            yield tuple(self.items())

# -------------------------------------------------------------------

'''
class Filter(WiseWorker):
    """Instances of the :class:`Filter` class forward only the subset
    of the received products that matches the filtering *query*.

    *query* must be a :class:`boing.core.Request` and it is used to
    filter the received products by using the method
    :meth:`Request.filter()<boing.core.Request.filter>`. *parent* must be a
    :class:`PyQt4.QtCore.QObject` and it defines the node's parent.

    Instances of the :class:`Filter` class do not have their own
    request and offer; they only propagate their sibling's ones with the
    exeption that the offer is also filtered using the query.

    """
    def __init__(self, query, parent=None):
        super().__init__(Request.NONE, WiseWorker.TUNNELING, parent=parent)
        self._query = assertIsInstance(query, Request)

    def query(self):
        """Return the :class:`Filter`'s query."""
        return self._query

    def setQuery(self, query):
        """Set the new :class:`Filter`'s *query*. *query*
        must be a :class:`boing.core.Request`."""
        self._query = assertIsInstance(query, Request)

    def _consume(self, products, producer):
        for product in products:
            subset = self.query().filter(product)
            if subset: self.postProduct(subset)

    def _propagateOffer(self):
        if self._consumer() is not None:
            if self.isPropagatingOffer():
                offers = (obs.offer() \
                              for obs in self._consumer().observed() \
                              if isinstance(obs, Producer))
                cumulated = sum(offers, Offer())
                filtered = Offer(iter=map(self.query().filter, cumulated))
                updated = self._selfOffer() + filtered
            else:
                updated = self._selfOffer()
            if self.offer()!=updated:
                self._cumulatedoffer = updated
                self.offerChanged.emit()
'''

# -------------------------------------------------------------------

'''class ArgumentFunctor(FunctionalNode):
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
                yield type(value)(functor(value))'''


class DiffArgumentFunctor(Functor):
    """It takes a functorfactory and for each different argument path,
    it creates a new functor which is applied to the argument
    value. The args must be a diff-based path so that functor can be
    removed depending on 'diff.removed' instances."""
    def __init__(self, functorfactory,
                 request, blender=Functor.MERGECOPY, parent=None):
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


# -------------------------------------------------------------------
# Encoder

class Encoder(Functor):

    def __init__(self, encoder, name, request, offer, blender, parent=None):
        super().__init__(request, offer, blender, parent=parent)
        self._encoder = assertIsInstance(encoder, BaseEncoder)
        self._name = name

    def encoder(self):
        raise NotImplementedError()

    def setEncoder(self, encoder):
        raise NotImplementedError()

    def _process(self, sequence, producer):
        for operands in sequence:
            for name, value in operands:
                yield ((name, self.encoder().encode(value)), )

# -------------------------------------------------------------------
# Decoder

class Decoder(Functor):

    def __init__(self, decoder, name, request, offer, blender, parent=None):
        super().__init__(request, offer, blender, parent=parent)
        self._decoder = assertIsInstance(decoder, BaseDecoder)
        self._name = name

    def decoder(self):
        raise NotImplementedError()

    def setDecoder(self, decoder):
        raise NotImplementedError()

    def _process(self, sequence, producer):
        for operands in sequence:
            for name, value in operands:
                for value in self.decoder().decode(value):
                    yield ((name, value), )


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
