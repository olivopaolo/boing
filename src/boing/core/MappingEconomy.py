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
from boing.core.ProducerConsumer import Producer, Consumer

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
        def __init__(self, ref):
            MappingConsumer.__init__(self, request=None)
            self.__ref = ref

        def _consume(self, products, producer):
            self.__ref()._postPipeline(products, producer)
            
    def __init__(self, productoffer=None, cumulate=None, parent=None):
        # FIXME: set productoffer
        MappingProducer.__init__(self, productoffer, cumulate, parent)
        """List of the registered post nodes."""
        self._post = []
        self._postConsumer = []
        """Forwards the produced products to the post Nodes before the
        standard forwarding."""
        self._postProducer = MappingProducer(productoffer)
        self._postProducer.requestChanged.connect(self.requestChanged)

    def post(self):
        return tuple(self._post)

    def addPost(self, node, mode=QtCore.Qt.QueuedConnection):
        self._post.append(node)
        if isinstance(node, Producer):
            postconsumer = HierarchicalProducer._PostConsumer(weakref.ref(self))
            postconsumer.subscribeTo(node, mode=mode)
            self._postConsumer.append(postconsumer)
        else:
            self._postConsumer.append(None)
        self._postProducer.addObserver(node, mode=mode)
        return self
    
    def _updateAggregateDemand(self):
        MappingProducer._updateAggregateDemand(self)
        cumulate = self.aggregateDemand()
        for post, consumer in zip(reversed(self._post), 
                                  reversed(self._postConsumer)):
            if isinstance(consumer, MappingConsumer):
                consumer.setRequest(cumulate)
                if isinstance(post, FunctionalNode):
                    if post.isActive():
                        if post.mode in (FunctionalNode.RESULT, 
                                        FunctionalNode.ARGSRESULT):
                            cumulate = post.request()
                        else:
                            cumulate = QPath.join(cumulate, post.args())
                else:                  
                    cumulate = QPath.join(cumulate, post.request())

    def isRequested(self, product):
        """A product is requested if it is demanded from one of the
        subscribed consumers or one of the posts."""
        return MappingProducer.isRequested(self, product) \
            or self._postProducer.aggregateDemand().test(product)

    def _postProduct(self, product):
        self._postPipeline((product,))

    def _postPipeline(self, products, current=None):
        stop = False
        i = 0 if current is None else self._post.index(current)+1
        while not stop:
            post = self._post[i] if i<len(self._post) else None
            if post is None:
                stop = True
                for product in products:
                    # Standard production
                    MappingProducer._postProduct(self, product)
            elif isinstance(post, Consumer) \
                    and (not isinstance(post, FunctionalNode) or post.isActive()):
                if isinstance(post, Node): stop = True
                # Forward the product to the post
                for product in products:
                    self._postProducer._postProductTo(product, post)
            i += 1
        

class HierarchicalConsumer(MappingConsumer):

    class _PreConsumer(MappingConsumer):
        def __init__(self, ref, request):
            MappingConsumer.__init__(self, request=request)
            self.__ref = ref

        def _consume(self, products, producer):
            self.__ref()._prePipeline(products, producer, isPre=True)

    def __init__(self, request=OnDemandProducer.ANY_PRODUCT, hz=None):
        MappingConsumer.__init__(self, request, hz)
        self._baserequest = self.request()
        """List of the registered pre nodes."""
        self._pre = []
        self._preConsumer = []
        """Forwards the received products to the pre Nodes before the
        standard consumption."""
        self._preProducer = MappingProducer()
        self._preProducer.requestChanged.connect(self._updateRequest)

    def pre(self):
        return tuple(self._pre)

    def addPre(self, node, mode=QtCore.Qt.QueuedConnection):
        self._pre.insert(0, node)
        if isinstance(node, Producer):
            preconsumer = HierarchicalConsumer._PreConsumer(weakref.ref(self),
                                                            self._baserequest)
            preconsumer.subscribeTo(node, mode=mode)
            self._preConsumer.insert(0, preconsumer)
        else:
            self._preConsumer.insert(0, None)
        self._preProducer.addObserver(node, mode=mode)
        return self

    def _updateRequest(self):
        cumulate = self._baserequest
        for pre, consumer in zip(reversed(self._pre), 
                                 reversed(self._preConsumer)):
            if isinstance(consumer, MappingConsumer):
                consumer.setRequest(cumulate)
                if isinstance(pre, FunctionalNode):
                    if pre.isActive():
                        if pre.mode in (FunctionalNode.RESULT, 
                                        FunctionalNode.ARGSRESULT):
                            cumulate = pre.request()
                        else:
                            cumulate = QPath.join(cumulate, pre.args())
                else:                  
                    cumulate = QPath.join(cumulate, pre.request())
        MappingConsumer.setRequest(self, cumulate)

    def setRequest(self, request):
        self._baseRequest =  QPath.QPath(request) \
            if request is not None and not isinstance(request, QPath.QPath) \
            else request
        self._updateRequest()

    def _refresh(self):
        for observable in self.queue():
            if isinstance(observable, Producer):
                self._prePipeline(observable.products(self), observable)

    def _prePipeline(self, products, producer, isPre=False):
        stop = False
        i = 0 if not isPre else self._pre.index(producer)+1
        while not stop:                    
            pre = self._pre[i] if i<len(self._pre) else None
            if pre is None:
                stop = True
                # Standard consumption                
                self._consume(products, producer)
            elif isinstance(pre, Consumer) \
                    and (not isinstance(pre, FunctionalNode) or pre.isActive()):
                if isinstance(pre, Node): stop = True
                # Forward the product to the pre
                for product in products:
                    self._preProducer._postProductTo(product, pre)
            i += 1

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

    DEFAULT_REQUEST = -1
    EMPTY_ARGS = (tuple(), tuple())

    '''
     - RESULT         the default request is defined as 'args' and it posts 
                      only the function result if it is requested;

     - ARGSRESULT     the default request is defined as 'args' and it posts 
                      the received product joined with the function result if the
                      result is requested;

     - MERGE          the default request is ANY_PRODUCT and it joins the 
                      received product and the function result if the result is
                      requested.

     - FORCE_FORWARD  the default request is ANY_PRODUCT and it forwards any
                      received products in any case.
    '''
    RESULT, ARGSRESULT, MERGE, FORCE_FORWARD = range(4)

    def __init__(self, args, target=None, template=None, 
                 mode=MERGE, reuse=False,
                 productoffer=None, cumulate=None,
                 request=DEFAULT_REQUEST, hz=None,
                 parent=None):
        self.__active = True
        # If request is not defined, it is set to args if it is not
        # supposed to forward all the products
        if request==FunctionalNode.DEFAULT_REQUEST: 
            request = args if mode==FunctionalNode.RESULT \
                or mode==FunctionalNode.ARGSRESULT \
                else OnDemandProducer.ANY_PRODUCT 
        Node.__init__(self, productoffer, cumulate, request, hz, parent)
        self._args = QPath.QPath(args) \
            if args is not None and not isinstance(args, QPath.QPath) \
            else args
        self._target = target
        self._template = template
        self.mode = mode
        self.reuse = reuse
        if self._template is not None:
            self._addTag(self._target, self._template)
            if self.mode!=FunctionalNode.FORCE_FORWARD:
                self.__active = False
                self.requestChanged.connect(self.__checkTarget)

    def isActive(self):
        return self.__active

    def setActive(self, active):
        if self.__active!=active:
            self.__active = active
            # Notify all OnDemandProducers it is subscribed to
            for observable in self.observed():
                if isinstance(observable, OnDemandProducer):
                    observable._requestChange(
                        self, self.request() if self.__active else None)

    def args(self):
        return self._args if self.__active else None

    def request(self):
        return Node.request(self) if self.__active else None
    
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
                    updated = False
                    for target, value in zip(targets, values):
                        if not updated:
                            if self.mode==FunctionalNode.RESULT:
                                result = utils.quickdict()
                            elif self.reuse:
                                result = product
                            else:
                                result = copy.deepcopy(product)
                            updated = True
                        split = target.split(".")
                        if len(split)==1: result[target] = value
                        else:
                            node = result
                            for key in split[1:-1]: 
                                node = node[key]
                            node[split[-1]] = value
                    if not updated: 
                        result = None if self.mode==FunctionalNode.RESULT \
                            else product
                else:
                    result = None if self.mode==FunctionalNode.RESULT \
                        else product
            else:
                result = None if self.mode==FunctionalNode.RESULT \
                    else product
            self._postProduct(result)
        
    def _function(self, paths, values):
        pass

    def __checkTarget(self):
        self.setActive(True if self.mode==FunctionalNode.FORCE_FORWARD \
                            or self._template is None \
                            or self._tag(self._target) \
                            else False)

