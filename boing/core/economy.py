# -*- coding: utf-8 -*-
#
# boing/core/economy.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import abc
import collections
import copy
import itertools
import sys
import weakref

from PyQt4 import QtCore

from boing.core.observer import SelectiveObservable, Observer
from boing.utils import assertIsInstance

# -------------------------------------------------------------------
# Offer

class _BaseOffer(collections.Sequence):
    pass

class _UndefinedOffer(_BaseOffer):

    def __contains__(self, item):
        return False

    def __getitem__(self, key):
        raise KeyError(key)

    def __iter__(self):
        return iter(tuple())

    def __len__(self):
        return 0

    def __str__(self):
        return "Offer.UNDEFINED"

    def __eq__(self, other):
        return other is Offer.UNDEFINED

    def __ne__(self, other):
        return not self==other

class Offer(tuple, _BaseOffer):
    
    def __new__(cls, *args, iter=None):
        """Offer can be direcly defined passing the products,
        e.g. Offer(p1, p2), or passing an iterable to the keyword
        argument *iter*, e.g. Offer(iter=[p1, p2])."""
        if iter is not None:
            if args: raise ValueError()
            else:
                rvalue = tuple.__new__(cls, iter)
        else:
            rvalue = tuple.__new__(cls, args)
        return rvalue

    def __str__(self):
        return "Offer(%s)"%", ".join(str(i) for i in self)

    def __add__(self, other):
        assertIsInstance(other, Offer)
        return Offer(iter=itertools.chain(self, other))

Offer.UNDEFINED = _UndefinedOffer()

# -------------------------------------------------------------------
# Request

class Request(metaclass=abc.ABCMeta):
    """Implements the Composite Pattern. Requests instances are immutable."""

    @abc.abstractmethod
    def test(self, product):
        """Returns True if *product* is requested; False otherwise."""
        raise NotImplementedError()

    @abc.abstractmethod
    def items(self, product):
        raise NotImplementedError()

    @abc.abstractmethod
    def filter(self, product):
        raise NotImplementedError()

    @abc.abstractmethod
    def filterout(self, product):
        raise NotImplementedError()

    @abc.abstractmethod
    def __eq__(self, other):
        raise NotImplementedError()

    def __ne__(self, other):
        return not self==other
        
    def __add__(self, other):
        if other is Request.ANY or self==other:
            rvalue = other
        elif other is Request.NONE:
            rvalue = self
        elif isinstance(other, Request):
            rvalue = _CompositeRequest(self, other)
        else: raise TypeError(
            "Expected type Request, not '%s'"%type(other).__name__)
        return rvalue

    @abc.abstractmethod
    def __hash__(self):
        raise NotImplementedError()

class _AnyRequest(Request):
            
    def test(self, product):
        return True

    def items(self, product):
        return product.items() if hasattr(product, "items") else (product,)

    def filter(self, product):
        return copy.copy(product)

    def filterout(self, product):
        return None

    def __eq__(self, other):
        return other is Request.ANY

    def __add__(self, other):
        if isinstance(other, Request):
            return self
        else: raise TypeError(
            "Expected type Request, not '%s'"%type(other).__name__)

    def __iadd__(self, other):
        if isinstance(other, Request):
            return self
        else: raise TypeError(
            "Expected type Request, not '%s'"%type(other).__name__)

    def __hash__(self):
        return hash(True)

    def __str__(self):
        return "Request.ANY"

class _NoneRequest(Request):
            
    def test(self, product):
        return False

    def items(self, product):
        return tuple()

    def filter(self, product):
        return None

    def filterout(self, product):
        return copy.copy(product)

    def __eq__(self, other):
        return other is Request.NONE

    def __add__(self, other):
        if isinstance(other, Request):
            return other
        else: raise TypeError(
            "Expected type Request, not '%s'"%type(other).__name__)

    def __hash__(self):
        return hash(False)

    def __str__(self):
        return "Request.NONE"

Request.ANY = _AnyRequest()
Request.NONE = _NoneRequest()

class _CompositeRequest(Request):
    
    def __init__(self, *requests):
        super().__init__()
        self._children = set()
        for req in requests:
            if isinstance(req, _CompositeRequest):
                self._children.update(req._children)
            elif isinstance(req, Request):
                self._children.add(req)
            else: raise TypeError(
                "Expected type Request, not '%s'"%type(req).__name__)

    def test(self, product):
        for child in self._children:
            if child.test(product): rvalue = True ; break
        else:
            rvalue = False
        return rvalue

    def items(self, product):
        return itertools.join(*(child.items(product) for child in self._children))

    def filter(self, product):
        rvalue = product
        for child in self._children:
            rvalue = child.filter(rvalue)
        return rvalue

    def filterout(self, product):
        rvalue = product
        for child in self._children:
            rvalue = child.filterout(rvalue)
        return rvalue

    def __eq__(self, other):
        return isinstance(other, _CompositeRequest) \
            and self._children==other._children

    def __hash__(self):
        raise NotImplementedError()


class FunctorRequest(Request):

    def __init__(self, test=None):
        super().__init__()
        self._customtest = assertIsInstance(test, None, collections.Callable)

    def test(self, product):
        if self._customtest is not None:
            return self._customtest(product)
        else:
            raise NotImplementedError()

    def items(self, product):
        return tuple() if not self.test(product) else \
            product.items() if hasattr(product, "items") else (product, )

    def filter(self, product):
        return copy.copy(product) if self.test(product) else None

    def filterout(self, product):
        return copy.copy(product) if not self.test(product) else None

    def __eq__(self, other):
        return isinstance(other, FunctorRequest) and \
            self._customtest==other._customtest

    def __hash__(self):
        return hash(self._customtest)

# -------------------------------------------------------------------
# Selectives

class Producer(SelectiveObservable):

    demandChanged = QtCore.pyqtSignal()
    offerChanged = QtCore.pyqtSignal()
    demandedOfferChanged = QtCore.pyqtSignal()

    def __init__(self, offer, tags=None, store=None, retrieve=None, 
                 parent=None, **kwargs):
        super().__init__(parent)
        self._aggregatedemand = Request.NONE
        self._offer = assertIsInstance(offer, _BaseOffer)
        self._demandedoffer = Offer()
        self._tags = assertIsInstance(dict() if tags is None else tags, dict)
        self._activetags = set()
        self.demandChanged.connect(self._refreshDemandedOffer)
        self.offerChanged.connect(self._refreshDemandedOffer)
        self._customstore = assertIsInstance(store, None, collections.Callable)
        self._customretrieve = assertIsInstance(retrieve, None, collections.Callable)
        # Connect slot passed as kwargs
        for key, value in kwargs.items():
            if key=="demandChanged": demandChanged = value
            elif key=="offerChanged": offerChanged = value
            elif key=="demandedOfferChanged": demandedOfferChanged = value
            else: raise TypeError(
                "'%s' is an invalid keyword argument for this function"%key)
        if "demandChanged" in locals(): 
            self.demandChanged.connect(demandChanged)
        if "demandedOfferChanged" in locals(): 
            self.demandedOfferChanged.connect(demandedOfferChanged)
        if "offerChanged" in locals(): 
            self.offerChanged.connect(offerChanged)

    def aggregateDemand(self):
        """Return the union of all the subscribed consumers' requests."""
        return self._aggregatedemand

    def offer(self):
        """Return the producer's offer."""
        return self._offer

    def setOffer(self, offer):
        if self._offer!=offer:
            self._offer = offer
            self.offerChanged.emit()

    def demandedOffer(self):
        """Return the producer's demanded offer."""
        return self._demandedoffer

    def meetsRequest(self, request):
        """Return True if the product's offer meets *request*."""
        assertIsInstance(request, Request)
        return True if self.offer() is Offer.UNDEFINED \
            else any(map(request.test, self.offer()))

    def isRequested(self, product=None, **kwargs):
        """FIXME: Return True if any of the subscribed consumers requires
        *product*; False otherwise"""
        for key, value in kwargs.items():
            if key=="tag": tag = value
            else: raise TypeError(
                "'%s' is an invalid keyword argument for this function"%key)        
        if product is None:
            if "tag" not in locals(): raise TypeError()
            else:
                rvalue = tag in self._activetags
        else:
            rvalue = self._aggregatedemand.test(product)
        return rvalue

    def _refreshAggregateDemand(self):
        cumulate = Request.NONE
        for obs in self.observers():
            if isinstance(obs, Consumer):
                cumulate += obs.request()
                if cumulate is Request.ANY: break
        #print(self, "_refreshAggregateDemand - ", self._aggregatedemand, cumulate)
        if self._aggregatedemand!=cumulate:
            self._aggregatedemand = cumulate
            self.demandChanged.emit()

    def _refreshDemandedOffer(self):
        """Update the demanded offerer using the current aggregate demand"""
        
        refresh = Offer(iter=filter(self._aggregatedemand.test, self.offer()))
        #print(self, "_refreshDemandedOffer - ", self._demandedoffer, refresh)
        if self._demandedoffer!=refresh:
            self._demandedoffer = refresh
            self._activetags = set(tag for tag, request in self._tags.items() \
                                       if any(map(request.test, 
                                                  self._demandedoffer)))
            self.demandedOfferChanged.emit()
            
    def addObserver(self, observer, mode=QtCore.Qt.QueuedConnection):
        rvalue = super().addObserver(observer, mode)
        if rvalue and isinstance(observer, Consumer):
            observer.requestChanged.connect(self._refreshAggregateDemand, 
                                            QtCore.Qt.QueuedConnection)
            self._refreshAggregateDemand()
        return rvalue

    def removeObserver(self, observer):
        rvalue = super().removeObserver(observer)
        if rvalue and isinstance(observer, Consumer):
            observer.requestChanged.disconnect(self._refreshAggregateDemand)
            self._refreshAggregateDemand()
        return rvalue

    def _checkRefs(self):
        super()._checkRefs()
        self._refreshAggregateDemand()

    def postProduct(self, product):
        records = tuple(self._filterRecords(product))
        if records: self._notifyFromRecords(records)
        return len(records)

    def _deliverProducts(self, products, consumer):
        consumer.productsDelivery(products, self)

    def _requireProducts(self, consumer):
        ref = self._getRef(consumer)
        if ref is None: raise Exception(
            "Unsubscribed consumers cannot get products: %s"%consumer)
        else:
            record = self._getRecord(ref=ref)
            record.notified = False
            self._retrieveAndDeliver(consumer)

    def _filterRecords(self, product):
        """Return an iterator over the record of each observer that
        must be triggerer due of having to post *product*."""
        for ref, record in self._SelectiveObservable__observers.items():
            observer = ref()
            if not isinstance(observer, Consumer) \
                    or observer.request().test(product) \
                    and self._store(product, observer) \
                    and not record.__dict__.get("notified", False):
                yield record

    def _notifyFromRecords(self, records):
        for record in records:
            record.notified = True
            record.trigger.emit(self)

    def _store(self, product, consumer):
        return self._customstore(self, product, consumer) \
            if self._customstore is not None \
            else self._defaultStore(product, consumer)
    
    def _retrieveAndDeliver(self, consumer):
        return self._customretrieve(self, consumer) \
            if self._customretrieve is not None \
            else self._defaultRetrieveAndDeliver(consumer)

    def _defaultStore(self, product, consumer):
        record = self._getRecord(consumer)
        if not hasattr(record, "products"):
            record.products = [product]
        else: 
            record.products.append(product)
        return record.products

    def _defaultRetrieveAndDeliver(self, consumer):
        """Retrive the products stored from *producer* for
        *consumer*, empty the storage and deliver the
        products. *record* is the data storage kept by *producer* for
        *consumer*."""
        record = self._getRecord(consumer)
        products = record.__dict__.get("products", list())
        record.products = list()
        self._deliverProducts(products, consumer)

class Consumer(Observer):

    class _InternalQObject(QtCore.QObject):
        requestChanged = QtCore.pyqtSignal()

    def __init__(self, request, consume=None, hz=None, **kwargs):
        super().__init__(hz=hz)
        self.__internal = Consumer._InternalQObject()
        self.__request = assertIsInstance(request, Request)
        self._customconsume = assertIsInstance(consume, None, collections.Callable)
        for key, value in kwargs.items():
            if key=="requestChanged": slot = value
            else: raise TypeError(
                "'%s' is an invalid keyword argument for this function"%key)
        if "slot" in locals(): self.requestChanged.connect(slot)
    
    def request(self):
        return self.__request

    def setRequest(self, request):
        """Set a new product request."""
        if self.__request!=request:
            self.__request = assertIsInstance(request, Request)
            self.requestChanged.emit()

    @property
    def requestChanged(self):
        return self.__internal.requestChanged

    def _react(self, observable):
        if isinstance(observable, Producer): 
            observable._requireProducts(self)
        else:
            pass

    def productsDelivery(self, products, producer=None):
        self._consume(products, producer)
            
    def _consume(self, products, producer):
        """The consumer normally must not modify the received
        products, because they could be shared with other consumers."""        
        return self._customconsume(self, products, producer) \
            if self._customconsume is not None \
            else None
        
# -------------------------------------------------------------------
# Hierarchical 

'''class HierarchicalProducer(Producer):

    class _PostProducer(Producer):
        def __init__(self, owner):
            super().__init__(Offer())
            self._owner = owner

        def offer(self):
            return self._owner._innerOffer()

    class _PostConsumer(Consumer):
        def __init__(self, owner):
            super().__init__(Request.NONE)
            self._owner = owner

        def request(self):
            return self._owner.aggregateDemand()

        def _consume(self, products, producer):
            for product in products:
                self._owner.postProduct(product)

    _innerOfferChanged = QtCore.pyqtSignal()

    def __init__(self, offer, *args, **kwargs):
        super().__init__(offer, *args, **kwargs)
        # FIXME: Replace self._post to self._posts
        self._post = []
        # Post producer
        self._postProducer = self._PostProducer(weakref.proxy(self))
        self._postProducer.demandChanged.connect(self._refreshPostDemand)
        self._innerOfferChanged.connect(self._postProducer.offerChanged)
        self._postProducer.offerChanged.connect(self.offerChanged)
        # Post consumer
        self._postConsumer = self._PostConsumer(weakref.proxy(self))
        self.demandChanged.connect(self._postConsumer.requestChanged)
        
    def posts(self):
        return iter(self._post)

    def addPost(self, post, mode=QtCore.Qt.DirectConnection):
        self._post.append(post)
        if isinstance(post, Producer):
            postconsumer = HierarchicalProducer._PostConsumer(weakref.proxy(self))
            postconsumer.subscribeTo(post, mode=mode)
            self._postConsumers.append(postconsumer)
        else:
            self._postConsumers.append(None)
        self._postProducer.addObserver(post, mode=mode)
        return self

    def setOffer(self, offer):
        if super().offer()!=offer:
            self._offer = offer
            self._innerOfferChanged.emit()

    def _innerOffer(self):
        return super().offer()

    def _cumulatePostDemand(self):
        cumulate = self.aggregateDemand()
        for post, consumer in zip(reversed(self._post), 
                                  reversed(self._postConsumers)):
            if consumer is not None: consumer.setRequest(cumulate)
            cumulate += post.request()
            # FIXME! CANNOT HANDLE THIS!
            #if isinstance(post, FilterOut):
            #    cumulate = QPath.subtract(cumulate, post.request())

    def isRequested(self, product=None, **kwargs):
        """A product is requested if it is demanded from one of the
        subscribed consumers or one of the posts."""
        rvalue = super().isRequested(product, **kwargs)
        return self._postProducer.isRequested(product) \
            if not rvalue and product is not None else rvalue

    def _refreshPostDemand(self):
        pass

    def offer(self):
        return self._postProducer.offer() if not self._post \
            else self._post[-1].offer()
        
    def postProduct(self, product):
        return super().postProduct(product) if not self._post \
            else self._postProducer.postProduct(product)

    def _postPipeline(self, products, current=None):
        for product in products:
            stop = False
            i = 0 if current is None else self._post.index(current)+1
            while not stop:
                post = self._post[i] if i<len(self._post) else None
                if post is None:
                    stop = True
                    # Standard production
                    super().postProduct(product)
                elif isinstance(post, Observer):
                    if self._postProducer.postProductTo(product, post) \
                            and isinstance(post, Node): 
                        stop = True
                i += 1'''

'''
class HierarchicalConsumer(Consumer):

    class _PreConsumer(Consumer):
        def __init__(self, consumer, request):
            super().__init__(request)
            self._consumer = consumer

        def _consume(self, products, producer):
            self._consumer._prePipeline(products, producer, isPre=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._baserequest = self._Consumer__request
        """List of the registered pre nodes."""
        self._pre = []
        self._preconsumers = []
        """Forwards the received products to the pre Nodes before the
        standard consumption."""
        self._preProducer = _CustomerProducer(offer=Offer.UNDEFINED)
        self._preProducer.demandChanged.connect(self._updateRequestPipeline, 
                                                QtCore.Qt.QueuedConnection)

    def pres(self):
        return iter(self._pre)

    def addPre(self, pre, mode=QtCore.Qt.DirectConnection):
        self._pre.insert(0, pre)
        if isinstance(pre, Producer):
            preconsumer = HierarchicalConsumer._PreConsumer(weakref.proxy(self),
                                                            self._baserequest)
            preconsumer.subscribeTo(pre, mode=mode)
            self._preconsumers.insert(0, preconsumer)
        else:
            self._preconsumers.insert(0, None)
        self._preProducer.addObserver(pre, mode=mode)
        return self

    def _updateRequestPipeline(self):
        cumulate = self._baserequest
        for pre, consumer in zip(reversed(self._pre), 
                                 reversed(self._preconsumers)):
            if consumer is not None: consumer.setRequest(cumulate)
            # Cumulate request and subtract filterout
            cumulate = cumulate + pre.request()
            # FIXME! CANNOT HANDLE THIS!
            #if isinstance(pre, FilterOut):
            #    cumulate = QPath.subtract(cumulate, pre.request())
        super().setRequest(cumulate)

    def setRequest(self, request):
        self._baserequest = request
        self._updateRequestPipeline()

    def productsDelivery(self, products, producer=None):
        self._prePipeline(products, producer)

    def _prePipeline(self, products, producer, isPre=False):
        i = 0 if not isPre else self._pre.index(producer)+1
        if i>=len(self._pre):  
            # Standard consumption                
            self._consume(products, producer)
        else:
            for product in products:
                stop = False
                while not stop:                    
                    if i>=len(self._pre):
                        stop = True
                        # Standard consumption                
                        self._consume((product, ), producer)
                    else:
                        pre = self._pre[i] 
                        if isinstance(pre, Consumer) \
                                and self._preProducer.postProductTo(product, pre) \
                                and isinstance(pre, Node):
                            stop = True
                    i += 1'''

# -------------------------------------------------------------------
# Nodes

class Worker(Producer, Consumer):

    def __init__(self, request, offer, tags=None, store=None, retrieve=None, 
                 parent=None, consume=None, hz=None, **kwargs):
        consumerkwargs = {} if "requestChanged" not in kwargs \
            else {"requestChanged": kwargs.pop("requestChanged")}
        Producer.__init__(self, offer, store, retrieve, parent, **kwargs)
        Consumer.__init__(self, request, consume, hz, **consumerkwargs)

    def __del__(self):
        Producer.__del__(self)
        Consumer.__del__(self)

    def _checkRefs(self):
        Producer._checkRefs(self)
        Consumer._checkRefs(self)


# -------------------------------------------------------------------
# Functor

class Functor(Worker):

    class Blender(object):
        @staticmethod    
        def blend(products, results):
            raise NotImplementedError()

    class MergeBlender(Blender):
        pass

    class ResultOnlyBlender(Blender):
        pass

    '''
    FIXME: The Functor determines its request and offer
    (i.e. wiserequest and wiseoffer variables) depending on the other
    producers and consumers it is attached to:

     - the request is deactivated if there aren't any consumers
       insterested to its offer (i.e. no items in demandedoffer);

     - the offer is deactivated if there are no producers
       that meet its request;

     Moreover, if blender is a MergeBlender, request and offer are
     propagated from its Observers and Observed.
    ''' 

    def __init__(self, args, offer, blender, process=None, **kwargs):
        super().__init__(request=args, offer=offer, **kwargs)
        self._active = False
        self._args = args
        self._wiserequest = Request.NONE
        self._wiseoffer = Offer()
        # demandedOffer and aggregateDemand influence the wise request
        self.demandedOfferChanged.connect(self._refreshWiseRequest,
                                          QtCore.Qt.QueuedConnection)
        self.demandChanged.connect(self._refreshWiseRequest, 
                                   QtCore.Qt.QueuedConnection)
        if not issubclass(blender, Functor.Blender): raise TypeError(
            "Expected Blender subclass, not '%s'"%blender)
        else:
            self._blender = blender
        self.__process = assertIsInstance(process, None, collections.Callable)        
        
    def _consume(self, products, producer):
        results = tuple() if not self.isActive() \
            else tuple(self._process(map(self._args.items, products), producer))
        products = self._blender.blend(products, results)
        for product in filter(None, products):
            self.postProduct(product)

    def _process(self, operands, producer):
        if self.__process is not None:
            return self.__process(operands, producer)
        else:
            raise NotImplementedError()

    def isActive(self):
        return self._active

    def request(self):
        return self._wiserequest

    def offer(self):
        return self._wiseoffer

    def _addObservable(self, observable):
        super()._addObservable(observable)
        if isinstance(observable, Producer):
            # Observed consumer's offer influence self wise offer
            observable.offerChanged.connect(self._refreshWiseOffer, 
                                            QtCore.Qt.QueuedConnection)
            self._refreshWiseOffer()

    def _removeObservable(self, observable):
        super()._removeObservable(observable)
        if isinstance(observable, Producer):
            observable.offerChanged.disconnect(self._refreshWiseOffer)
            self._refreshWiseOffer()

    def _refreshWiseRequest(self):
        # Self request is demanded only if its offer is requested from
        # a subscribed consumer. Moreover, if using a MergeBlender, it
        # propagates its consumers' request.
        if super().offer() is Offer.UNDEFINED \
                or any(p in self.demandedOffer() for p in super().offer()):
            self._active = True
            refreshed = super().request()+self.aggregateDemand() \
                if issubclass(self._blender, Functor.MergeBlender) \
                else super().request()
        else:
            self._active = False
            refreshed = self.aggregateDemand() \
                if issubclass(self._blender, Functor.MergeBlender) \
                else Request.NONE
        if self.request()!=refreshed:
            self._wiserequest = refreshed
            self.requestChanged.emit()

    def _refreshWiseOffer(self):        
        # Self offer is proposed only if its request is met by at least one 
        # registered Producer. Moreover, if using a MergeBlender, it
        # propagates its producers' offer.
        inneroffer = super().offer() \
            if any(obs.meetsRequest(self._args) for obs in self.observed() \
                       if isinstance(obs, Producer)) \
            else Offer()
        refreshed = sum(
            (obs.offer() for obs in self.observed() if isinstance(obs, Producer)),
            inneroffer) \
            if issubclass(self._blender, Functor.MergeBlender) else inneroffer
        if self.offer()!=refreshed:
            self._wiseoffer = refreshed
            self.offerChanged.emit()


class Identity(Functor):

    class _NoBlender(Functor.MergeBlender):
        @staticmethod    
        def blend(products, results):
            for product in products:
                yield product
    
    def __init__(self, **kwargs):
        super().__init__(Request.NONE, Offer(), blender=Identity._NoBlender, 
                         process=lambda operands, producer: None, **kwargs)
        
# -------------------------------------------------------------------

def dumpGraph(origins, fd=sys.stdout, maxdepth=None, indent=6):
    # print("dumpGraph", origins, fd)
    memo = []
    for node in origins:
        dumpNode(node, memo, fd, 0, maxdepth, indent)


def dumpNode(node, memo, fd, level, maxdepth, indent):
    # print("dumpNode", memo, fd)
    if memo is None: memo = []
    if node in memo:
        fd.write("Node: %d"%memo.index(node))
    else:
        memo.append(node)
        base = " "*(level*indent)
        fd.write(base+"%d: %s\n"%(len(memo), type(node)))
        if isinstance(node, Consumer):
            fd.write(base+"   request = %s\n"%node.request())
            '''if isinstance(node, FilterOut):
                filterout = node.request()
                if filterout is not None: filterout = repr(str(filterout))
                fd.write(base+"  filterout = %s\n"%filterout)'''
            # if isinstance(node, HierarchicalConsumer):
            #     pres = tuple(node.pres())
            #     fd.write(base+"  pre = [")
            #     if not pres: fd.write("]\n")
            #     elif maxdepth is None or level<maxdepth:
            #         fd.write(base+"\n\n")                
            #         for pre in pres:
            #             dumpNode(pre, memo, fd, level+1, maxdepth, indent)
            #         fd.write(base+"  ]\n")                
            #     else:
            #         fd.write("...]\n")
            #     fd.write(base+"  _baserequest = %s\n"%node._baserequest)
        if isinstance(node, Producer):
            # fd.write(base+"   activetags = %s\n"%node._activetags)
            # if isinstance(node, HierarchicalProducer):
            #     fd.write(base+"   _postProducer:\n")
            #     fd.write(base+"     offer = %s\n"%str(node._postProducer.offer()))
            #     fd.write(base+"     aggregateDemand = %s\n"%(
            #             node._postProducer.aggregateDemand()))
            #     fd.write(base+"     demandedoffer = %s\n"%str(
            #             node._postProducer.demandedOffer()))
            #     posts = list(node.posts())
            #     fd.write(base+"   posts = [")                    
            #     if not posts: fd.write("]\n")
            #     elif maxdepth is None or level<maxdepth:
            #         fd.write(base+"\n\n")                
            #         for post in posts:
            #             dumpNode(post, memo, fd, level+1, maxdepth, indent)
            #         fd.write(base+"  ]\n")                
            #     else:
            #         fd.write("...]\n")
            fd.write(base+"   offer = %s\n"%str(node.offer()))
            fd.write(base+"   aggregateDemand = %s\n"%node.aggregateDemand())
            fd.write(base+"   demandedoffer = %s\n"%str(node.demandedOffer()))
            fd.write(base+"   observers = [")
            if not tuple(node.observers()):
                fd.write("]\n")
            elif maxdepth is None or level<maxdepth:
                fd.write("\n\n")                
                for observer in node.observers():
                    dumpNode(observer, memo, fd, level+1, maxdepth, indent)
                fd.write(base+"  ]\n\n")
            else:
                fd.write("...]\n\n")
