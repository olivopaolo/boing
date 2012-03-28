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
                                  MappingProducer.__test, parent)
        """Union of all the subscribed consumers' requests."""
        self.__aggregatedemand = None
        self.demandChanged.connect(self._updateAggregateDemand)
        self.__fseq = 0
        self.__info__source = str(self)
        # Tag support
        self.__tags = {}
        self.demandChanged.connect(self._updateTags)
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
        return self.__aggregatedemand.test(product) \
            if self.__aggregatedemand is not None else False

    def _postProduct(self, product):
        self.__fseq += 1
        if not isinstance(product, collections.Mapping):
            raise TypeError(
                "postProduct() argument must be a Mapping, not '%s'"%type(product))
        if self._tag("__timetag__"): 
            product["__timetag__"] = datetime.datetime.now()
        if self._tag("__fseq__"): product["__fseq__"] = self.__fseq
        if self._tag("__source__"): product["__source__"] = self.__info__source
        OnDemandProducer._postProduct(self, product)

    @staticmethod
    def __test(request, product):
        """Return True if 'product' matches 'request'; False otherwise."""
        if request is None: rvalue = False
        elif str(request)==OnDemandProducer.ANY_PRODUCT:
            rvalue = True
        else:
            rvalue = request.test(product)
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
        self._postProducer.demandChanged.connect(self.demandChanged, 
                                                 QtCore.Qt.QueuedConnection)
        
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
            if consumer is not None: consumer.setRequest(cumulate)
            # Cumulate request and subtract filterout
            cumulate = QPath.join(cumulate, post.request())
            if isinstance(post, FilterOut):
                cumulate = QPath.subtract(cumulate, post.request())

    def isRequested(self, product):
        """A product is requested if it is demanded from one of the
        subscribed consumers or one of the posts."""
        return MappingProducer.isRequested(self, product) \
            or self._postProducer.aggregateDemand() is not None \
            and self._postProducer.aggregateDemand().test(product) 

    def _postProduct(self, product):
        self._postPipeline((product,))

    def _postPipeline(self, products, current=None):
        for product in products:
            stop = False
            i = 0 if current is None else self._post.index(current)+1
            while not stop:
                post = self._post[i] if i<len(self._post) else None
                if post is None:
                    stop = True
                    # Standard production
                    MappingProducer._postProduct(self, product)
                elif isinstance(post, Consumer):
                    if self._postProducer._postProductTo(product, post) \
                            and isinstance(post, Node): 
                        stop = True
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
        self._preProducer.demandChanged.connect(self._updateRequestPipeline, 
                                                QtCore.Qt.QueuedConnection)

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

    def _updateRequestPipeline(self):
        cumulate = self._baserequest
        for pre, consumer in zip(reversed(self._pre), 
                                 reversed(self._preConsumer)):
            if consumer is not None: consumer.setRequest(cumulate)
            # Cumulate request and subtract filterout
            cumulate = QPath.join(cumulate, pre.request())
            if isinstance(pre, FilterOut):
                cumulate = QPath.subtract(cumulate, pre.request())
        MappingConsumer.setRequest(self, cumulate)

    def setRequest(self, request):
        self._baserequest =  QPath.QPath(request) \
            if request is not None and not isinstance(request, QPath.QPath) \
            else request
        self._updateRequestPipeline()

    def _refresh(self):
        for observable in self.queue():
            if isinstance(observable, Producer):
                self._prePipeline(observable.products(self), observable)

    def _prePipeline(self, products, producer, isPre=False):
        for product in products:                           
            stop = False
            i = 0 if not isPre else self._pre.index(producer)+1
            while not stop:                    
                pre = self._pre[i] if i<len(self._pre) else None
                if pre is None:
                    stop = True
                    # Standard consumption                
                    self._consume((product, ), producer)
                elif isinstance(pre, Consumer):
                    if self._preProducer._postProductTo(product, pre) \
                            and isinstance(pre, Node):
                        stop = True
                i += 1

# -------------------------------------------------------------------

class Node(HierarchicalProducer, HierarchicalConsumer):

    """If a node is transparent, its request is always set to the same
    as its aggregate demand."""
    TRANSPARENT = object()

    def __init__(self, productoffer=None, cumulate=None, request=TRANSPARENT, 
                 hz=None, parent=None):
        HierarchicalProducer.__init__(self, productoffer, cumulate, parent)
        HierarchicalConsumer.__init__(
            self, None if request is Node.TRANSPARENT else request, hz)
        self._transparent = request==Node.TRANSPARENT
        self.demandChanged.connect(self._applyDemandToRequest) 

    def __del__(self):
        HierarchicalProducer.__del__(self)
        HierarchicalConsumer.__del__(self)

    def _checkRef(self):
        HierarchicalProducer._checkRef(self)
        HierarchicalConsumer._checkRef(self)

    def isTransparent(self):
        return self._transparent

    def setTransparent(self, value):
        if self._transparent!=value:
            self._transparent = value
            self.setRequest(self.aggregateDemand() if self._transparent \
                                else None)

    def _applyDemandToRequest(self):
        if self._transparent: self.setRequest(self.aggregateDemand())

    def _consume(self, products, producer):
        raise NotImplementedError()

class TunnelNode(Node):
    """It forwards everything it receives to the subscribed consumers."""
    def _consume(self, products, producer):
        for product in products:
            self._postProduct(product)


class Filter(Node):
    """Filters the received products using a QPath query and it posts
    the results."""
    def __init__(self, query, request=Node.TRANSPARENT, hz=None, parent=None):
        super().__init__(request=request, hz=hz, parent=parent)
        self.__query = query \
            if query is None or isinstance(query, QPath.QPath) \
            else QPath.QPath(query)        

    def query(self):
        return self.__query

    def setQuery(self, query):
        self.__query = query \
            if query is None or isinstance(query, QPath.QPath) \
            else QPath.QPath(query)        

    def _consume(self, products, producer):
        for product in products:
            subset = self.__query.filter(product, deepcopy=False) \
                if self.__query is not None else None
            if subset: self._postProduct(subset)


class FilterOut(Node):
    """Filters out everything it requires."""
    def __init__(self, request, hz=None, parent=None):
        super().__init__(request=request, hz=hz, parent=parent)

    def _consume(self, products, producer):
        for product in products:
            subset = self.request().filterout(product)
            if subset: self._postProduct(subset)


class FunctionalNode(Node):

    __EMPTY_ARGS = (tuple(), tuple())

    '''
     - RESULT         the default request is defined as 'args' and it posts 
                      only the function result if it is requested;

     - MERGE          the default request is ANY_PRODUCT and it joins the 
                      received product and the function result if the result is
                      requested.

     - MERGECOPY      '''      
    RESULT, MERGE, MERGECOPY = (object() for i in range(3))

    def __init__(self, args, target=None, template=None, mode=MERGE,
                 productoffer=None, cumulate=None, hz=None, 
                 parent=None, **kwargs):
        self._active = True
        self._args = args \
            if args is None or isinstance(args, QPath.QPath) \
            else QPath.QPath(args)
        request = self._args
        for key, value in kwargs.items():
            if key=="request": request = value
            else: raise TypeError(
                "'%s' is an invalid keyword argument for this function"%key)        
        super().__init__(productoffer, cumulate, request, hz, parent)
        self._target = target
        self._template = template
        self._mode = mode
        if self._template is not None:
            self._active = False
            self._addTag(self._target, self._template)
            self.demandChanged.connect(self._checkTarget)

    def isActive(self):
        return self._active

    def _checkTarget(self):
        if self._active!=(self._template is None or self._tag(self._target)):
            self._active = not self._active
            for observable in self.observed():
                if isinstance(observable, OnDemandProducer):
                    observable._requestChange(self, self.request())

    def request(self):
        return super().request() if self._active else None
    
    def _consume(self, products, producer):
        for product in products:
            if self._template is None or self._tag(self._target):
                argpaths, argvalues = self._args.items(product) \
                    if self._args is not None \
                    else FunctionalNode.__EMPTY_ARGS
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
                            if self._mode==FunctionalNode.RESULT:
                                result = utils.quickdict()
                            elif self._mode==FunctionalNode.MERGE:
                                result = product
                            else:
                                result = copy.deepcopy(product)
                            updated = True
                        split = target.split(".")
                        if len(split)==1: result[target] = value
                        else:
                            node = result
                            for key in split[:-1]: 
                                node = node[key]
                            node[split[-1]] = value
                    if not updated: 
                        result = None if self._mode==FunctionalNode.RESULT \
                            else product
                else:
                    result = None if self._mode==FunctionalNode.RESULT \
                        else product
            else:
                result = None if self._mode==FunctionalNode.RESULT \
                    else product
            if result is not Node: self._postProduct(result)
        
    def _function(self, paths, values):
        pass
