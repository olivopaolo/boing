# -*- coding: utf-8 -*-
#
# boing/core/economy.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

"""The economy module provides classes that implement the
producer-consumer problem.

The Producer and Consumer classes are build over the Observer design
pattern of the module boing.core.observer: the Producer is an
Observable object enabled to post products; a consumer is an Observer
object that can subscribe itself to many producers. When a producer
has a new product, it triggers the registered consumers; the triggered
consumers will immediately or at regular time interval demand the
producer the new products.

A producer can be registered to multiple consumers. Each product is
shared within different consumers, therefore a consumer SHOULD NOT
modify any received product, unless it is supposed to be the only
consumer.

Consumers have a request. Each time a producer has a new product, for
each registered consumer, it check if the consumer's request matches
the current product and only in such case it triggers the consumer.

A consumer's request must be an instance of the class Request. The
requests "any product" and "no product" are available. The class
Request implements the Composite design pattern.

Producers have an offer, which is a list of product templates. A
producer, using its own offer, can say if it can meet a consumer's
request.

The Worker inherits both the Producer and Consumer classes and it is
used as base class for defining processing nodes. By connecting
producers, workers and consumers it is possible to create processing
pipelines.

"""

import abc
import collections
import copy
import itertools
import sys
import weakref

from PyQt4 import QtCore

from boing.utils import assertIsInstance

# -------------------------------------------------------------------
# Offer

class Offer(tuple):
    """An offer defines the list of products that a producer
    advertises to be its deliverable objects.
    
    """
    pass

    class UndefinedProduct:
        """UndefinedProduct instances can be used to define a
        producer's offer, when the real offer cannot be defined a
        priori. This avoids to have empty offers, when they cannot be
        predeterminated.

        """
        def __repr__(self): return "Product.UNDEFINED"    
        def __eq__(self, other): return isinstance(other, Offer.UndefinedProduct)
        def __ne__(self, other): return not isinstance(other, Offer.UndefinedProduct)
    
    def __new__(cls, *args, iter=None):
        """Constructor.

        Offer can be direcly constructed passing the sequence of
        products, e.g. Offer(p1, p2), or passing an iterable to the
        keyword argument *iter*, e.g. Offer(iter=[p1, p2]).

        """
        l = lambda item: item is not None
        if iter is not None:
            if args: raise ValueError()
            else:
                rvalue = tuple.__new__(cls, filter(l, iter))
        else:
            rvalue = tuple.__new__(cls, filter(l, args))
        return rvalue

    def __repr__(self): 
        return "Offer(%s)"%", ".join(str(i) for i in self)

    def __add__(self, other):
        if other is None:
            rvalue = self
        elif isinstance(other, Offer):
            rvalue = Offer(iter=itertools.chain(
                    self, filter(lambda item: item not in self, other)))
        else:
            rvalue = NotImplemented
        return rvalue

    def __radd__(self, other):
        return self if other is None else NotImplemented

# -------------------------------------------------------------------
# Request

class Request(metaclass=abc.ABCMeta):
    """The Request abstract class defines objects for filtering
    products.  Each consumer has got a request so that producers know
    if it is useful or not to deliver a product to a consumer.

    Request.NONE and Request.ANY define respectively a no product and
    any product requests.
    
    The Request class implements the Composite design
    pattern. Composite requests can be obtained simply adding singular
    requests, e.g. comp = r1 + r2. Request.NONE is the identity
    element of Request sum.

    Request instances are immutable objects.

    """
    @abc.abstractmethod
    def test(self, product):
        """Return whether *product* matches the request."""
        raise NotImplementedError()

    @abc.abstractmethod
    def items(self, product):
        """Return an iterator over the *product*'s items ((key, value)
        pairs) that match the request, if *product* can be subdivided, otherwise
        return the pair (None, *product)."""
        raise NotImplementedError()

    @abc.abstractmethod
    def filter(self, product):
        """Return the subset of *product* that matches the request, if
        *product* can be subdivided, otherwise return *product*, if
        product matches the request, else return None."""
        raise NotImplementedError()

    @abc.abstractmethod
    def filterout(self, product):
        """Return the subset of *product* that does not match the
        request, if *product* can be subdivided, otherwise return
        *product*, if product does not match the request, else return
        None."""
        raise NotImplementedError()

    @abc.abstractmethod
    def __hash__(self): raise NotImplementedError()

    @abc.abstractmethod
    def __eq__(self, other): raise NotImplementedError()

    def __ne__(self, other): return not self==other
        
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

class _AnyRequest(Request):

    def __init__(self):
        pass
            
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

    def __repr__(self):
        return "Request.ANY"

class _NoneRequest(Request):

    def __init__(self):
        pass
            
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

    def __repr__(self):
        return "Request.NONE"

Request.ANY = _AnyRequest()
Request.NONE = _NoneRequest()

class _CompositeRequest(Request):
    
    def __init__(self, *requests):
        super().__init__()
        self._children = set()
        for req in requests:
            if req is Request.NONE:
                continue
            elif isinstance(req, _CompositeRequest):
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


class LambdaRequest(Request):
    """
    The LambdaRequest is a Request that can be initialized using a
    lambda function.
    """
    def __init__(self, test=None):
        super().__init__()
        self._customtest = assertIsInstance(test, None, collections.Callable)

    def test(self, product):
        if self._customtest is not None:
            return self._customtest(product)
        else:
            raise NotImplementedError()

    def items(self, product):
        return tuple() if not self.test(product) \
            else product.items() if hasattr(product, "items") else (product, )

    def filter(self, product):
        return copy.copy(product) if self.test(product) else None

    def filterout(self, product):
        return copy.copy(product) if not self.test(product) else None

    def __eq__(self, other):
        return isinstance(other, LambdaRequest) \
            and self._customtest==other._customtest

    def __hash__(self):
        return hash(self._customtest)

# -------------------------------------------------------------------
# Producer

from boing.core.observer import Observable, Observer

class Producer(Observable):
    """
    A Producer is an observable object enabled to post products to
    a set of subscribed consumers. 

    When a producer is demanded to posts a product, for each
    registered consumer it tests the product with the consumer's
    request and only if the match is valid it triggers the consumer.

    Each Producer has an Offer (a list of product templates), so it
    can say if a priori it can meet a consumer's request.
    """

    class ConfigurableOffer:
        """The ConfigurableOffer class provides the method
        *setOffer*, which enables to set the offer of the
        producer.  Inherit both Producer and ConfigurableOffer to
        grant such behaviour, e.g. :

           class MyProducer(Producer, Producer.ConfigurableOffer):
               pass
        
        """
        def setOffer(self, offer):
            """Set *offer* as the new producer's offer."""
            if self._offer!=offer:
                self._offer = offer
                self.offerChanged.emit()

    demandChanged = QtCore.pyqtSignal()
    """Signal emitted when the aggregate demand changes."""

    offerChanged = QtCore.pyqtSignal()
    """Signal emitted when its own offer changes."""

    demandedOfferChanged = QtCore.pyqtSignal()
    """Signal emitted when its own demanded offer changes."""

    def __init__(self, offer, tags=None, store=None, retrieve=None, 
                 parent=None):
        """Constructor.

        *offer* must be an instance of Offer.

        *tags* must be a dict or None.
        
        *store* can be a callable object to be used as a handler for
        storing posted products (see *_store* for the handler arguments)
        or None.
        
        *retrieve* can be a callable object to be used as a handler
        for retrieving stored products (see *_retrieveAndDeliver* for
        the handler arguments) or None.

        *parent* defines the consumer's parent.

        """
        super().__init__(parent)
        self._aggregatedemand = Request.NONE
        self._offer = assertIsInstance(offer, Offer)
        self._demandedoffer = Offer()
        self._tags = assertIsInstance(dict() if tags is None else tags, dict)
        self._activetags = set()
        self.demandChanged.connect(self._refreshDemandedOffer)
        self.offerChanged.connect(self._refreshDemandedOffer)
        self.__store = assertIsInstance(store, None, collections.Callable)
        self.__retrieve = assertIsInstance(retrieve, None, collections.Callable)
        
    def aggregateDemand(self):
        """Return the union of all the subscribed consumers' requests."""
        return self._aggregatedemand

    def offer(self):
        """Return the producer's offer."""
        return self._offer

    def demandedOffer(self):
        """Return the producer's demanded offer."""
        return self._demandedoffer

    def meetsRequest(self, request):
        """Return whether the product's offer meets *request*."""
        assertIsInstance(request, Request)
        return request is Request.NONE or any(map(request.test, self.offer()))

    def isRequested(self, product=None, **kwargs):
        """Return whether any of the subscribed consumers requires
        *product*."""
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

    def postProduct(self, product):
        """Post *product*. In concrete terms, it triggers the
        registered consumers that require *product*, then it stores
        the product."""
        records = tuple(self._filterRecords(product))
        if records: self._notifyFromRecords(records)
        return len(records)

    def _filterRecords(self, product):
        """Return an iterator over the record of each observer that
        must be triggerer due of posting *product*."""
        for ref, record in self._Observable__observers.items():
            observer = ref()
            if not isinstance(observer, Consumer) \
                    or observer.request().test(product) \
                    and self._store(product, observer) \
                    and not record.__dict__.get("notified", False):
                yield record

    def _store(self, product, consumer):
        """Store *product* while waiting that *consumer* retrives it."""
        # Call custom function if defined, otherwise use default method.
        return self.__store(self, product, consumer) \
            if self.__store is not None \
            else self._defaultStore(product, consumer)

    def _requireProducts(self, consumer):
        """Notify that *consumer* required the products stored for it.""" 
        ref = self._getRef(consumer)
        if ref is None: raise Exception(
            "Unsubscribed consumers cannot get products: %s"%consumer)
        else:
            record = self._getRecord(ref=ref)
            record.notified = False
            self._retrieveAndDeliver(consumer)

    def _retrieveAndDeliver(self, consumer):
        """Retrive all the products stored for *consumer* and deliver them."""
        # Call custom function if defined, otherwise use default method.
        return self.__retrieve(self, consumer) \
            if self.__retrieve is not None \
            else self._defaultRetrieveAndDeliver(consumer)

    def _deliverProducts(self, products, consumer):
        """Deliver *products* to *consumer*."""
        consumer.productsDelivery(products, self)

    def _defaultStore(self, product, consumer):
        """Enqueue *product* into the *consumer* product queue."""
        record = self._getRecord(consumer)
        if not hasattr(record, "products"):
            record.products = [product]
        else: 
            record.products.append(product)
        return record.products

    def _defaultRetrieveAndDeliver(self, consumer):
        """Retrive the products stored for *consumer*, empty the
        storage and deliver the products."""
        record = self._getRecord(consumer)
        products = record.__dict__.get("products", list())
        record.products = list()
        self._deliverProducts(products, consumer)

    def _refreshAggregateDemand(self):
        """Recalculate the aggregate demand."""
        cumulate = Request.NONE
        for obs in self.observers():
            if isinstance(obs, Consumer):
                cumulate += obs.request()
                if cumulate is Request.ANY: break
        if self._aggregatedemand!=cumulate:
            self._aggregatedemand = cumulate
            self.demandChanged.emit()

    def _refreshDemandedOffer(self):
        """Recalculate the demanded offer."""        
        refresh = Offer(iter=filter(self._aggregatedemand.test, self.offer()))
        if self._demandedoffer!=refresh:
            self._demandedoffer = refresh
            self._activetags = set(tag for tag, request in self._tags.items() \
                                       if any(map(request.test, 
                                                  self._demandedoffer)))
            self.demandedOfferChanged.emit()
            
    def addObserver(self, observer, mode=QtCore.Qt.QueuedConnection, child=False):
        rvalue = super().addObserver(observer, mode, child)
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

    def _notifyFromRecords(self, records):
        """Notify the observers associated to *records*."""
        for record in records:
            record.notified = True
            record.trigger.emit(self)

    def __add__(self, other):
        if other is None:
            rvalue = self
        elif isinstance(other, Composite):
            # Let the Composite '__radd__' method be used
            rvalue = NotImplemented
        elif isinstance(other, Worker):
            other.subscribeTo(self, child=True)
            rvalue = _CompositeProducer(other)
        elif isinstance(other, Consumer):
            # Warning: such composite is closed
            self.addObserver(other)
            composite = Composite()
            other.setParent(composite)
            self.setParent(composite)
            rvalue = composite
        else:
            rvalue = NotImplemented
        return rvalue

    def __radd__(self, other):
        return self if other is None else NotImplemented

    def _debugData(self):
        rvalue = super()._debugData()
        rvalue["offer"] = self.offer()
        rvalue["demandedOffer"] = self.demandedOffer()
        rvalue["aggregateDemand"] = self.aggregateDemand()
        return rvalue

# -------------------------------------------------------------------
# Consumer

class Consumer(Observer):
    """A Consumer is an observer object that can be subscribed to many
    producers for receiving their products. When a producer posts a
    product, it triggers the registered consumers; the triggered
    consumers will immediately or at regular time interval demand the
    producer the new products.

    Many consumers can be subscribed to a single producer. Each new
    product is actually shared within the different consumers,
    therefore a consumer SHOULD NOT modify any received product,
    unless it is supposed to be the only consumer.

    Consumers have a request. When a producer is demanded to posts a
    product, it tests the product with the consumer's request and only
    if the match is valid it triggers the consumer.

    A consumer's request must be an instance of the class Request. The
    requests "any product" and "no product" are available.

    """

    class ConfigurableRequest:
        """The ConfigurableRequest class provides the method
        *setRequest*, which enables to set the request of the
        consumer.  Inherit both Consumer and ConfigurableRequest to
        grant such behaviour, e.g. :

           class MyConsumer(Consumer, Consumer.ConfigurableRequest):
               pass
        
        """
        def setRequest(self, request):
            """Set *request* as the consumer's request."""
            if self._request!=request:
                self._request = assertIsInstance(request, Request)
                self.requestChanged.emit()

    class _InternalQObject(QtCore.QObject):
        requestChanged = QtCore.pyqtSignal()

    @property
    def requestChanged(self):
        """Signal emitted when the new consumer's request changes."""
        return self.__internal.requestChanged

    def __init__(self, request, consume=None, hz=None, parent=None):
        """Constructor.

        *request* must be an instance of Request.

        *consume* can be a callable object to be used as a handler for
        consuming received products (see *_consume* for the handler arguments)
         or None.
        
        *hz* defines when the consumer should react to the observervables'
         notifications. Accepted values:
          - None   : immediately ;
          - 0      : never ;
          - float  : at the selected frequency (in hz).

        *parent* defines the consumer's parent.

        """
        super().__init__(hz=hz, parent=parent)
        self.__internal = Consumer._InternalQObject()
        self._request = assertIsInstance(request, Request)
        self.__consume = assertIsInstance(consume, None, collections.Callable)
    
    def request(self):
        """Return the consumer's request."""
        return self._request

    def _react(self, observable):
        """If *observable* is a producer, require its products."""
        if isinstance(observable, Producer): 
            observable._requireProducts(self)

    def productsDelivery(self, products, producer=None):
        """Slot for delivering *products*."""
        self._consume(products, producer)
            
    def _consume(self, products, producer):
        """Consume *products* posted from *producer*."""
        # Call custom function if defined, otherwise use default method.
        return self.__consume(self, products, producer) \
            if self.__consume is not None \
            else None

    def __add__(self, other):
        return self if other is None else NotImplemented

    def __radd__(self, other):
        return self if other is None else NotImplemented

    def _debugData(self):
        rvalue = super()._debugData()
        rvalue["request"] = self.request()
        return rvalue

# -------------------------------------------------------------------
# Request and offer propagation

class _PropagatingProducer(Producer):

    class ConfigurableOffer(Producer.ConfigurableOffer):          
        def setOffer(self, offer):
            if self._offer!=offer:
                self._offer = offer
                self._propagateOffer()

    def __init__(self, consumer, offer, tags=None, store=None, retrieve=None, 
                 parent=None):
        super().__init__(offer, tags, store, retrieve, parent)
        self._cumulatedoffer = offer
        self.__cons = assertIsInstance(consumer, None, Consumer)
        if self.__cons is not None:
            self.__cons.observableAdded.connect(self.__followOffer)
            self.__cons.observableRemoved.connect(self.__unfollowOffer)

    def offer(self):
        return self._cumulatedoffer

    def isPropagatingOffer(self):
        return True

    def _selfOffer(self):
        return super().offer()

    def _consumer(self):
        return self.__cons

    def _setConsumer(self, consumer):
        if self.__cons is not None:
            self.__cons.observableAdded.disconnect(self.__followOffer)
            self.__cons.observableRemoved.disconnect(self.__unfollowOffer)
        self.__cons = consumer
        self.__cons.observableAdded.connect(self.__followOffer)
        self.__cons.observableRemoved.connect(self.__unfollowOffer)

    def _propagateOffer(self):
        if self._consumer() is not None:
            updated = \
                sum((obs.offer() for obs in self._consumer().observed() \
                         if isinstance(obs, Producer)),
                    self._selfOffer()) \
                if self.isPropagatingOffer() \
                else self._selfOffer()
            if self.offer()!=updated:
                self._cumulatedoffer = updated
                self.offerChanged.emit()

    def __followOffer(self, observable):
        if isinstance(observable, Producer):
            # Observed consumer's offer influence self wise offer
            observable.offerChanged.connect(self._propagateOffer, 
                                            QtCore.Qt.QueuedConnection)
            self._propagateOffer()

    def __unfollowOffer(self, observable):
        if isinstance(observable, Producer):
            observable.offerChanged.disconnect(self._propagateOffer)
            self._propagateOffer()


class _PropagatingConsumer(Consumer):

    class ConfigurableRequest(Consumer.ConfigurableRequest):
        def setRequest(self, request):
            """Set *request* as the consumer's request."""
            if self._request!=request:
                self._request = assertIsInstance(request, Request)
                self._propagateRequest()
    
    def __init__(self, producer, request, consume=None, hz=None, parent=None):
        super().__init__(request, consume, hz, parent)
        self._cumulatedrequest = request
        self.__prod = assertIsInstance(producer, None, Producer)
        if self.__prod is not None:
            # demandedOffer and aggregateDemand influence the cumulated request
            self.__prod.demandedOfferChanged.connect(self._propagateRequest, 
                                                     QtCore.Qt.QueuedConnection)
            self.__prod.demandChanged.connect(self._propagateRequest, 
                                              QtCore.Qt.QueuedConnection)
        self.requestChanged.connect(self._propagateRequest)
        
    def request(self):
        return self._cumulatedrequest

    def isPropagatingRequest(self):
        return True

    def _selfRequest(self):
        return super().request()

    def _producer(self):
        return self.__prod

    def _setProducer(self, producer):
        if self.__prod is not None:
            self.__prod.demandedOfferChanged.disconnect(self._propagateRequest)
            self.__prod.demandChanged.disconnect(self._propagateRequest)
        self.__prod = producer
        self.__prod.demandedOfferChanged.connect(self._propagateRequest,
                                                 QtCore.Qt.QueuedConnection)
        self.__prod.demandChanged.connect(self._propagateRequest,
                                          QtCore.Qt.QueuedConnection)

    def _propagateRequest(self):
        updated = self._selfRequest()
        if self.isPropagatingRequest() and self._producer() is not None: 
            updated += self._producer().aggregateDemand()
        if self.request()!=updated:
            self._cumulatedrequest = updated
            self.requestChanged.emit()

# -------------------------------------------------------------------
# Worker

class Worker:
    """Workers can normally propagate requests and offers, i.e. the
    requests of all the connected consumers are summed to the worker's
    own request to form its real request and the offers of all
    the connected producers are summed to the worker's own offer to
    form its real offer.    
    """
    pass

class _PropagatingWorker(Worker, _PropagatingProducer, _PropagatingConsumer):

    def __init__(self, request, offer, 
                 tags=None, store=None, retrieve=None, 
                 consume=None, hz=None, parent=None):
        _PropagatingProducer.__init__(self, None,
                                      offer, tags, store, retrieve, parent)
        _PropagatingConsumer.__init__(self, weakref.proxy(self),
                                      request, consume, hz,
                                      parent=None)
        self._setConsumer(weakref.proxy(self))

    def __del__(self):
        _PropagatingProducer.__del__(self)
        _PropagatingConsumer.__del__(self)

    def _checkRefs(self):
        _PropagatingProducer._checkRefs(self)
        _PropagatingConsumer._checkRefs(self)

    def clear(self):
        _PropagatingProducer.clear(self)
        _PropagatingConsumer.clear(self)

    def __add__(self, other):
        if other is None:
            rvalue = self
        elif isinstance(other, Composite):
            # Let the Composite '__radd__' method be used
            rvalue = NotImplemented
        elif isinstance(other, Worker):
            self.addObserver(other)
            rvalue = _CompositeWorker(consumers=[self], producers=[other])
        elif isinstance(other, Consumer):
            self.addObserver(other, child=True)
            rvalue = _CompositeConsumer(self)
        else:
            rvalue = NotImplemented
        return rvalue

    def _debugData(self):
        rvalue = _PropagatingConsumer._debugData(self)
        rvalue.update(_PropagatingProducer._debugData(self))
        return rvalue

    def _debugSiblings(self):
        rvalue = _PropagatingConsumer._debugSiblings(self)
        rvalue.update(_PropagatingProducer._debugSiblings(self))
        return rvalue


class Identity(_PropagatingWorker):
    
    def __init__(self, store=None, retrieve=None, hz=None, parent=None):
        super().__init__(request=Request.NONE, offer=Offer(), 
                         store=store, retrieve=retrieve, hz=hz, parent=parent)

    def _consume(self, products, producer):
        for product in products:
            self.postProduct(product)
        
# -------------------------------------------------------------------
# Composite

class _ForwardingConsumer(_PropagatingConsumer):
    def _consume(self, products, producer):
        producer = self._producer()
        if producer is not None:
            for product in products:
                producer.postProduct(product)

class Composite(QtCore.QObject):
    pass

class _CompositeProducer(_PropagatingProducer, Composite):
    
    def __init__(self, *producers, parent=None):
        super().__init__(_ForwardingConsumer(None, Request.NONE),
                         offer=Offer(), parent=parent)
        self._consumer()._setProducer(weakref.proxy(self))
        for prod in producers:
            assertIsInstance(prod, Producer)
            self._consumer().subscribeTo(prod, child=True)

    def pushPost(self, worker):
        assertIsInstance(worker, Worker)
        for child in self._consumer().children():
            child.removeObserver(self._consumer())
            worker.subscribeTo(child, child=True)
        self._consumer().subscribeTo(worker, child=True)
                        
    def __add__(self, other):
        if other is None:
            rvalue = self
        elif isinstance(other, Worker):
            self.pushPost(other)
            rvalue = self
        elif isinstance(other, Consumer):
            # Warning! Such Composite is closed.
            self.addObserver(other)
            composite = Composite()
            other.setParent(composite)
            self.setParent(composite)
            rvalue = composite
        else:
            rvalue = NotImplemented
        return rvalue

    def _debugSiblings(self):
        rvalue = super()._debugSiblings()
        rvalue.update(consumer=self._consumer())
        rvalue.move_to_end('consumer', last=False)
        return rvalue        
    
class _CompositeConsumer(_ForwardingConsumer, Composite):
    
    def __init__(self, *consumers, parent=None):
        super().__init__(_PropagatingProducer(None, Offer()),
                         Request.NONE, parent=parent)        
        self._producer()._setConsumer(weakref.proxy(self))
        for cons in consumers:
            assertIsInstance(cons, Consumer)
            self._producer().addObserver(cons, child=True)

    def pushPre(self, worker):
        assertIsInstance(worker, Worker)
        for child in self._producer().children():
            child.unsubscribeFrom(self._producer())
            worker.addObserver(child, child=True)
        self._producer().addObserver(worker, child=True)

    def __add__(self, other):
        return self if other is None else NotImplemented

    def __radd__(self, other):
        if other is None:
            rvalue = self
        elif isinstance(other, Worker):
            self.pushPre(other)
            rvalue = self
        elif isinstance(other, Producer):
            # Warning! Such Composite is closed.
            self.subscribeTo(other)
            composite = Composite()
            other.setParent(composite)
            self.setParent(composite)
            rvalue = composite
        else:
            rvalue = NotImplemented
        return rvalue

    def _debugSiblings(self):
        rvalue = super()._debugSiblings()
        rvalue.update(producer=self._producer())
        rvalue.move_to_end('producer', last=False)
        return rvalue        


class _CompositeWorker(_CompositeProducer, _CompositeConsumer, Worker):

    def __init__(self, consumers, producers, parent=None):
        _CompositeProducer.__init__(self, *producers, parent=parent)
        _CompositeConsumer.__init__(self, *consumers)

    def __del__(self):
        _CompositeProducer.__del__(self)
        _CompositeConsumer.__del__(self)

    def _checkRefs(self):
        _CompositeProducer._checkRefs(self)
        _CompositeConsumer._checkRefs(self)

    def clear(self):
        _CompositeProducer.clear(self)
        _CompositeConsumer.clear(self)        
            
    def __add__(self, other):
        if other is None:
            rvalue = self
        elif isinstance(other, Worker):
            self.pushPost(other)
            rvalue = self #_CompositeWorker(consumers=[self], producers=[other])
        elif isinstance(other, Consumer):
            # Warning! this case destroyes self
            consumers = self._producer().children()
            for consumer in consumers:
                consumer.unsubscribeFrom(self._producer())                
            rvalue = _CompositeConsumer(*consumers)
            for producer in self._consumer().children():
                producer.removeObserver(self._consumer())
                producer.addObserver(other, child=True)
                producer.setParent(rvalue)
        else:
            rvalue = NotImplemented
        return rvalue

    def __radd__(self, other):
        if other is None:
            rvalue = self
        elif isinstance(other, Worker):
            self.pushPre(other)
            rvalue = self
        elif isinstance(other, Producer):
            # Warning! this case destroyes self
            producers = self._consumer().children()
            for producer in producers:
                producer.removeObserver(self._consumer())                
            rvalue = _CompositeProducer(*producers)
            for consumer in self._producer().children():
                consumer.unsubscribeFrom(self._producer())
                consumer.subscribeTo(other, child=True)
                consumer.setParent(rvalue)
        else:
            rvalue = NotImplemented
        return rvalue

    def _debugData(self):
        rvalue = _CompositeConsumer._debugData(self)
        rvalue.update(_CompositeProducer._debugData(self))
        return rvalue

    def _debugSiblings(self):
        rvalue = _CompositeConsumer._debugSiblings(self)
        rvalue.update(_CompositeProducer._debugSiblings(self))
        return rvalue

# -------------------------------------------------------------------
# Functor

class WiseWorker(_PropagatingWorker):
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

    class _Forcing: pass
    ACTIVATED = _Forcing()
    DEACTIVATED = _Forcing()
    NONE = _Forcing()

    TUNNELING = object()
    """Use *TUNNELING* as the worker Offer, when the worker is
    supposed to process and then forward a subset of the products it
    receives. This is necessary since the worker cannot have a
    predefined offer, but it always depend from the offer of the
    observed producers."""
    
    
    def __init__(self, request, offer, **kwargs):
        self._tunneling = offer is WiseWorker.TUNNELING
        super().__init__(request, 
                         Offer() if offer is WiseWorker.TUNNELING else offer,
                         **kwargs)
        self._active = False
        self._forced = None

    def isActive(self):
        # The worker is active only if its offer is requested from
        # a subscribed consumer.
        return self._active

    def isTunneling(self):
        """Return True if the worker is forwarding a subset of the
        products it receives."""
        return self._tunneling

    def forcing(self):
        return self._forced

    def setForcing(self, forcing):
        assertIsInstance(forcing, WiseWorker._Forcing)
        self._forced = forcing
        self._propagateRequest()

    def _selfRequest(self): 
        return super()._selfRequest() if self.isActive() else Request.NONE

    def _selfOffer(self):
        # Self offer is proposed only if its request is met by at least one 
        # registered Producer.
        satisfied = False
        for obs in self.observed():
            if isinstance(obs, Producer) \
                    and obs.meetsRequest(super()._selfRequest()):
                satisfied = True ; break
        return super()._selfOffer() if satisfied else Offer()

    def _propagateRequest(self):
        self._refreshActive()
        super()._propagateRequest()

    def _refreshActive(self):
        if self.forcing() is WiseWorker.ACTIVATED:
            self._active = True
        if self.forcing() is WiseWorker.DEACTIVATED:
            self._active = False
        else:
            offer = self.offer() if self.isTunneling() else super()._selfOffer()
            self._active = any(p in self.demandedOffer() for p in offer)

    def _debugData(self):
        rvalue = super()._debugData()
        rvalue["active"] = self.isActive()
        rvalue.move_to_end('active', last=False)
        rvalue.move_to_end('id', last=False)
        return rvalue

class Functor(WiseWorker):  

    class Blender(metaclass=abc.ABCMeta):
        @abc.abstractmethod
        def blend(self, products, results):
            raise NotImplementedError()

    class MergeBlender(Blender):
        def __repr__(self): return "Blender.MERGE"

    class ResultOnlyBlender(Blender):
        def __repr__(self): return "Blender.RESULTONLY"

    def __init__(self, args, offer, blender, process=None, **kwargs):
        super().__init__(request=args, offer=offer, **kwargs)
        if not isinstance(blender, Functor.Blender): raise TypeError(
            "Expected Blender subclass, not '%s'"%blender)
        else:
            self._blender = blender
        self.__process = assertIsInstance(process, None, collections.Callable)

    def blender(self):
        return self._blender
        
    def _consume(self, products, producer):
        results = tuple() if not self.isActive() \
            else self._process(map(self._selfRequest().items, products),
                               producer)
        products = self.blender().blend(products, 
                                        results if results is not None else tuple())
        for product in filter(None, products):
            self.postProduct(product)

    def _process(self, operands, producer):
        if self.__process is not None:
            return self.__process(operands, producer)
        else:
            raise NotImplementedError()
        
    def isPropagatingRequest(self):
        return isinstance(self.blender(), Functor.MergeBlender)

    def isPropagatingOffer(self):
        return self.isTunneling() \
            or isinstance(self.blender(), Functor.MergeBlender)

    def _debugData(self):
        rvalue = super()._debugData()
        rvalue["blender"] = self.blender()
        return rvalue
