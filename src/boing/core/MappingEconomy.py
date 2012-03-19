# -*- coding: utf-8 -*-
#
# boing/core/MappingEconomy.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import copy
import datetime
import itertools
import weakref

from PyQt4 import QtCore

import boing.utils as utils
import boing.utils.QPath as QPath

from boing.core.OnDemandProduction import OnDemandProducer, SelectiveConsumer
from boing.core.ProducerConsumer import Producer

class MappingProducer(OnDemandProducer):

    class TagRecord(object):
        def __init__(self, template):
            self.template = template
            self.requested = False

    def __init__(self, productoffer=None, cumulate=None, parent=None):
        # FIXME: set productoffer
        OnDemandProducer.__init__(self, productoffer, cumulate, 
                                  MappingProducer.filter, parent)
        """Union of all the subscribed consumers' requests."""
        self.__aggregatedemand = QPath.QPath(None)
        self.requestChanged.connect(self._updateAggregateDemand)
        self.__fseq = 0
        # Tag support
        self.__tags = {}
        self.requestChanged.connect(self._updateTags)
        self.__info__source = str(self)
        self._addTag("__timetag__", {"__timetag__": datetime.datetime.now()})
        self._addTag("__fseq__", {"__fseq__": self.__fseq})
        self._addTag("__source__", {"__source__": self.__info__source})

    def aggregateDemand(self):
        """Return the union of all the subscribed consumers' requests."""
        return self.__aggregatedemand

    def _updateAggregateDemand(self):
        requests = (record.request for record in self._consumers.values())
        self.__aggregatedemand = QPath.join(*requests)

    def _addTag(self, tag, template):
        record = MappingProducer.TagRecord(template)
        self.__tags[tag] = record

    def _updateTags(self):
        for record in self.__tags.values():
            record.requested = self.isRequested(record.template)

    def _tag(self, tag):
        """Returns True if 'tag' is requested."""
        record = self.__tags.get(tag)
        return False if record is None else record.requested

    def isRequested(self, product):
        # Faster than the parent class implementation
        return self.__aggregatedemand.test(product)

    def _postProduct(self, product):
        self.__fseq += 1
        if not isinstance(product, collections.Mapping):
            product = {"product":product}
        if self._tag("__timetag__"): 
            product["__timetag__"] = datetime.datetime.now()
        if self._tag("__fseq__"):  product["__fseq__"] = self.__fseq
        if self._tag("__source__"): product["__source__"] = self.__info__source
        OnDemandProducer._postProduct(self, product)

    @staticmethod
    def filter(product, request):
        """Return the subset of 'product' that matches 'request' or
        None."""
        if request==OnDemandProducer.ANY_PRODUCT:
            rvalue = product
        elif request is None:
            rvalue = None
        else:
            rvalue = request.filter(product)
        return rvalue


class MappingConsumer(SelectiveConsumer):
    """A MappingConsumer's request is always a QPath."""
    
    def __init__(self, request=OnDemandProducer.ANY_PRODUCT, hz=None):
        if request is not None and not isinstance(request, QPath.QPath):
            request = QPath.QPath(request)
        SelectiveConsumer.__init__(self, request, hz)

    def setRequest(self, request):
        if request is not None and not isinstance(request, QPath.QPath):
            request = QPath.QPath(request)
        SelectiveConsumer.setRequest(self, request)

# -------------------------------------------------------------------

class HierarchicalProducer(MappingProducer):

    class _PostConsumer(MappingConsumer):
        """It forwards all the products of the parent
        HierarchicalProducer's posts as products of the
        HierarchicalProducer itself."""
        def __init__(self, ref):
            MappingConsumer.__init__(self, request=None)
            self.__ref = ref

        def setRequest(self, request):
            # Ensure that __callfseq__ is requested
            MappingConsumer.setRequest(
                self, QPath.join(request, "__callfseq__|__callsource__"))

        def _consume(self, products, producer):
            if isinstance(producer, FunctionalNode):
                for result in products:
                    fseq = result.pop("__callfseq__")
                    source = result.pop("__callsource__")
                    # FIXME: add check __callsource__
                    product, waiting = self.__ref()._postbuffer[fseq]
                    waiting.remove(producer)
                    utils.deepupdate(product, result, reuse=True)
                    if not waiting:
                        del self.__ref()._postbuffer[fseq]
                        MappingProducer._postProduct(self.__ref(), product)
            else:
                for p in products:
                    MappingProducer._postProduct(self.__ref(), p)

    def __init__(self, productoffer=None, cumulate=None, parent=None):
        # FIXME: set productoffer
        MappingProducer.__init__(self, productoffer, cumulate, parent)
        """List of the registered post nodes."""
        self._post = []
        """List of the post FunctionalNodes which are active."""
        self._postfunction = []
        """Products that are waiting for the post functional nodes' result."""
        self._postbuffer = {}
        """Forwards the produced products to the post Nodes before the
        standard forwarding."""
        self._postProducer = MappingProducer(productoffer)
        self._postProducer.requestChanged.connect(self._postRequestChanged)
        """Receives the products from the post Nodes and it forwards them
        as standard products."""
        self._postConsumer = HierarchicalProducer._PostConsumer(weakref.ref(self))

    def addPost(self, node, mode=QtCore.Qt.DirectConnection):        
        self._post.append(node)
        self._postProducer.addObserver(node, mode=mode)
        self._postConsumer.subscribeTo(node, mode=mode)
        return self

    def _postRequestChanged(self):
        # Update enabled post
        self._postfunction = list(post for post in self._post \
                                      if isinstance(post, FunctionalNode) \
                                      and post.isEnabled())
        self.requestChanged.emit()
    
    def _updateAggregateDemand(self):
        MappingProducer._updateAggregateDemand(self)
        # The standard aggregate demand is set as the request of the
        # postConsumer
        self._postConsumer.setRequest(self.aggregateDemand())

    def isRequested(self, product):
        """A product is requested if it is demanded from one of the
        subscribed consumers or one of the posts."""
        return MappingProducer.isRequested(self, product) \
            or self._postProducer.aggregateDemand().test(product)

    def _postProduct(self, product):
        # print(self, "postfunction", self._postfunction)
        # print(self, "post:", self._post)
        if self._postfunction:
            fseq = self._postProducer._MappingProducer__fseq+1
            self._postbuffer[fseq] = (product, self._postfunction[:])
            self._postProducer._postProduct(product)
        else:
            # Standard production
            MappingProducer._postProduct(self, product)
            # Forward the product to the posts
            if self._post: self._postProducer._postProduct(product)


class HierarchicalConsumer(MappingConsumer):

    class _PreConsumer(MappingConsumer):
        """It forwards all the products of the parent
        HierarchicalConsumer's pre as products of the
        HierarchicalConsumer itself."""
        def __init__(self, ref, request):
            MappingConsumer.__init__(self, request=request)
            self.__ref = ref
            self.__buffer = list()

        def setRequest(self, request):
            # Ensure that __callfseq__ is requested
            MappingConsumer.setRequest(
                self, QPath.join(request, "__callfseq__|__callsource__"))

        def _consume(self, products, producer):
            if isinstance(producer, FunctionalNode):
                for result in products:
                    fseq = result.pop("__callfseq__")
                    source = result.pop("__callsource__")
                    # FIXME: add check __callsource__
                    product, waiting = self.__ref()._prebuffer[fseq]
                    waiting.remove(producer)
                    utils.deepupdate(product, result, reuse=True)
                    if not waiting:
                        del self.__ref()._prebuffer[fseq]
                        self.__buffer.append(product)
                if self.__buffer:
                    self.__ref()._consume(self.__buffer, producer)
                    self.__buffer = list()
            else:
                self.__ref()._consume(products, producer)

    def __init__(self, request=OnDemandProducer.ANY_PRODUCT, hz=None):
        MappingConsumer.__init__(self, request, hz)
        """List of the registered pre nodes."""
        self._pre = []
        """List of pre FunctionalNodes which are active."""
        self._prefunction = []
        """Products that are waiting for the pre functional nodes' result."""
        self._prebuffer = {}
        """Forwards the received products to the pre Nodes before the
        standard consumption."""
        self._preProducer = MappingProducer()
        self._preProducer.requestChanged.connect(self._updateRequest)
        """Receives the products from the pre Nodes and it passes them
        to the standard consumption."""
        # The standard request is set as the one of the preConsumer
        self._preConsumer = HierarchicalConsumer._PreConsumer(weakref.ref(self), 
                                                              request)

    def addPre(self, node, mode=QtCore.Qt.DirectConnection, serial=None):
        self._pre.append(node)
        self._preProducer.addObserver(node, mode=mode)
        self._preConsumer.subscribeTo(node, mode=mode)
        return self

    def _updateRequest(self):
        # Update enabled post
        self._prefunction = list(pre for pre in self._pre \
                                     if isinstance(pre, FunctionalNode) \
                                     and pre.isEnabled())        
        # pre & self
        join = QPath.join(self._preConsumer.request(), 
                          self._preProducer.aggregateDemand())
        MappingConsumer.setRequest(self, join)

    def setRequest(self, request):
        # The standard request is set as the one of the preConsumer
        self._preConsumer.setRequest(request)
        self._updateRequest()

    def _refresh(self):
        for observable in self.queue():
            if isinstance(observable, Producer):
                products = observable.products(self)
                # print(self, "prefunction:", self._prefunction)
                # print(self, "pre", self._pre)
                if self._prefunction:
                    for product in products:
                        fseq = self._preProducer._MappingProducer__fseq+1
                        self._prebuffer[fseq] = (product, self._prefunction[:])
                        self._preProducer._postProduct(product)
                else:
                    # Standard consumption
                    self._consume(products, observable)
                    # Forward the product to the pres
                    if self._pre:
                        for product in products:
                            self._preProducer._postProduct(product)

# -------------------------------------------------------------------

class Node(HierarchicalProducer, HierarchicalConsumer):
    def __init__(self, productoffer=None, cumulate=None, 
                 request=OnDemandProducer.ANY_PRODUCT, hz=None,
                 parent=None):
        HierarchicalProducer.__init__(self, productoffer, cumulate, parent)
        HierarchicalConsumer.__init__(self, request, hz)

    def __del__(self):
        HierarchicalProducer.__del__(self)
        HierarchicalConsumer.__del__(self)

    def _checkRef(self):
        HierarchicalProducer._checkRef(self)
        HierarchicalConsumer._checkRef(self)


class FunctionalNode(Node):

    _DEFAULT = -1
    EMPTY_ARGS = (tuple(), tuple())

    """For all the products it receives, it must post a product with
    the same fseq of the received product."""
    def __init__(self, args, target=None, template=None, forward=False,
                 productoffer=None, cumulate=None, 
                 request=_DEFAULT, hz=None,
                 parent=None):
        # If request is not defined, it is set to args if it is not
        # supposed to forward all the products
        if request==FunctionalNode._DEFAULT: 
            request = OnDemandProducer.ANY_PRODUCT if forward else args 
        # Ensure that __fseq__ and __source__ are requested
        Node.__init__(self, productoffer, cumulate, 
                      QPath.join(request, "__fseq__|__source__"), hz, parent)
        self._args = QPath.QPath(args) \
            if args is not None and not isinstance(args, QPath.QPath) \
            else args
        self._target = target
        self._template = template
        self._forward = forward
        if self._template is not None:
            self._addTag(self._target, self._template)
            if not self._forward:
                self.setEnabled(False)
                self.requestChanged.connect(self.__checkTarget)

    def _consume(self, products, producer):
        for product in products:
            if self._template is None or self._tag(self._target):
                argpaths, argvalues = self._args.items(product) \
                    if self._args is not None \
                    else FunctionalNode.EMPTY_ARGS
                if self._target is None:
                    targets = argpaths
                    values = self._function(argpaths, argvalues)
                elif isinstance(self._target, collections.Callable):
                    targets = self._target(argpaths)
                    values = self._function(argpaths, argvalues)
                else:
                    targets = itertools.repeat(self._target)
                    values = self._function(argpaths, argvalues)
                if values is not None:
                    # Apply values to targets
                    copied = False
                    for target, value in zip(targets, values):
                        if not copied:
                            result = copy.deepcopy(product) if self._forward \
                                else utils.quickdict()
                            copied = True
                        split = target.split(".")
                        if len(split)==1: result[target] = value
                        else:
                            node = result
                            for key in split[1:-1]: 
                                node = node[key]
                            node[split[-1]] = value
                    if not copied: 
                        result = copy.copy(product) if self._forward \
                            else utils.quickdict()
                else:
                    result = copy.copy(product) if self._forward \
                        else utils.quickdict()
            else:
                result = copy.copy(product) if self._forward \
                    else utils.quickdict()
            result["__callfseq__"] = product["__fseq__"]
            result["__callsource__"] = product["__source__"]            
            self._postProduct(result)
        
    def _function(self, paths, values):
        pass

    def __checkTarget(self):
        self.setEnabled(True if self._forward \
                            or self._template is None \
                            or self._tag(self._target) \
                            else False)

