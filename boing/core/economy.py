# -*- coding: utf-8 -*-
#
# boing/core/economy.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

"""The module :mod:`boing.core.economy` provides an implementation of
the producer-consumer problem.

The :class:`Producer` and :class:`Consumer` classes are build over the
Observer design pattern of the module :mod:`boing.core.observer`: the
Producer is an Observable object enabled to post products; a consumer
is an Observer object that can subscribe itself to many
producers. When a producer has a new product, it triggers the
registered consumers; the triggered consumers will immediately or at
regular time interval demand the producer the new products.

A :class:`Worker` object is both a :class:`Producer` and a
:class:`Consumer` and it is used as base class for defining processing
nodes. By connecting producers, workers and consumers it is possible
to create processing pipelines.

A :class:`WiseWorker` is a :class:`Worker` able to automatically
detect whenever it should not propose its own offer or its own
request; this is done in order to save computational time.

The :class:`Functor` class is practical base class for inheriting
custom processing :class:`Worker` objects. Instead of implementing the
classic :meth:`Consumer._consume` method, the :class:`Functor` proposes the
more powerfull method :meth:`Functor._process`.

Multiple :class:`Producer`, :class:`Consumer` and :class:`Worker`
instances can be composed into :class:`Composite` objects. There are
three types of composites:

- a :class:`CompositeProducer` works as it was a single producer;
- a :class:`CompositeConsumer` works as it was a single consumer;
- a :class:`CompositeWorker` works as it was a single worker;

"""

import abc
import collections
import copy
import itertools
import sip
import sys
import weakref

from PyQt4 import QtCore

from boing.utils import assertIsInstance

# -------------------------------------------------------------------
# Offer

class Offer(tuple):

    def __new__(cls, *args, iter=None):
        """   An :class:`Offer` defines the list of products that a producer
        advertises to be its deliverable objects.

        .. note:: A producer's offer only estimates the products that
           are normally produced. There is no guarantee that such products
           will ever be posted, neither that products that do not match the
           offer won't be produced.

        :const:`Offer.UNDEFINED` can be used to define the producer's
        offer, when the real offer cannot be defined a priori. This avoids
        to have empty offers, when they cannot be predeterminated.

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

    def __copy__(self):
        return Offer(iter=self)

    def __deepcopy__(self, memo):
        ref = id(self)
        if ref in memo: rvalue = memo[ref]
        else:
            rvalue = Offer(iter=map(lambda item: copy.deepcopy(item, memo),
                                    self))
            memo[ref] = rvalue
        return rvalue

    class _UndefinedProduct:
        def __repr__(self): return "Offer.UNDEFINED"

Offer.UNDEFINED = Offer._UndefinedProduct()

# -------------------------------------------------------------------
# Request
class Request(metaclass=abc.ABCMeta):
    """The class :class:`Request` is an abstract class used by
    :class:`Consumer` objects for specifing the set of products they
    are insterested to. The method :meth:`test` is used to check
    whether a product matches the request.

    :const:`Request.NONE` and :const:`Request.ANY` define respectively
    a "no product" and "any product" requests.

    :class:`Request` objects may also indicate the internal parts of a
    product to which a producer may be interested. The method
    :meth:`items` returns the sequence of the product's parts a
    producer is interested to.

    The class :class:`Request` implements the design pattern
    "Composite": different requests can be combined into a single
    request by using the sum operation (e.g. :code:`comp = r1 +
    r2`). A composite request matches the union of the products that
    are matched by the requests whom it is
    composed. :const:`Request.NONE` is the identity element of the sum
    operation.

    :class:`Request` objects are immutable.

    """

    @abc.abstractmethod
    def test(self, product):
        """Return whether the *product* matches the request."""
        raise NotImplementedError()

    @abc.abstractmethod
    def items(self, product):
        """Return an iterator over the *product*'s internal parts
        (i.e. (key, value) pairs) that match the request."""
        raise NotImplementedError()

    @abc.abstractmethod
    def __hash__(self): raise NotImplementedError()

    @abc.abstractmethod
    def __eq__(self, other): raise NotImplementedError()
    def __ne__(self, other): return not self==other

    def __add__(self, other):
        assertIsInstance(other, Request)
        return other if other is Request.ANY or self==other else \
            self if other is Request.NONE else \
            _CompositeRequest(self, other)

    # @abc.abstractmethod
    # def filter(self, product):
    #     """The method :meth:`filter` tries to create a new
    #     object composed only by the demanded parts. Return the subset
    #     of *product* that matches the request, if *product* can be
    #     subdivided, otherwise return *product*, if product matches the
    #     request, else return None."""
    #     raise NotImplementedError()

    # @abc.abstractmethod
    # def filterout(self, product):
    #     """The method :meth:`filterout` tries to create a new object
    #     composed only by the elements that are not required. Return the
    #     subset of *product* that does not match the request, if
    #     *product* can be subdivided, otherwise return *product*, if
    #     product does not match the request, else return None."""
    #     raise NotImplementedError()


class _AnyRequest(Request):

    def test(self, product): return True

    def items(self, product):
        return product.items() if isinstance(product, collections.Mapping) \
            else enumerate(product) if isinstance(product, collections.Sequence) \
            else ((k,v) for k,v in dict(product) if not k.startswith("_"))

    def __eq__(self, other): return other is Request.ANY

    def __add__(self, other):
        assertIsInstance(other, Request)
        return self

    def __iadd__(self, other):
        assertIsInstance(other, Request)
        return self

    def __hash__(self): return hash(True)
    def __repr__(self): return "Request.ANY"

    # def filter(self, product): return copy.copy(product)
    # def filterout(self, product): return None


class _NoneRequest(Request):

    def test(self, product): return False
    def items(self, product): return tuple()
    def __eq__(self, other): return other is Request.NONE

    def __add__(self, other):
        assertIsInstance(other, Request)
        return other

    def __hash__(self): return hash(False)
    def __repr__(self): return "Request.NONE"

    # def filter(self, product): return None
    # def filterout(self, product): return copy.copy(product)

Request.ANY = _AnyRequest()
Request.NONE = _NoneRequest()

class _CompositeRequest(Request):

    def __init__(self, *requests):
        super().__init__()
        cumulate = set()
        for req in requests:
            assertIsInstance(req, Request)
            if req is Request.NONE:
                continue
            elif isinstance(req, _CompositeRequest):
                cumulate.update(req._children)
            else:
                cumulate.add(req)
        self._children = frozenset(cumulate)

    def test(self, product):
        for child in self._children:
            if child.test(product): rvalue = True ; break
        else:
            rvalue = False
        return rvalue

    def items(self, product):
        return itertools.join(*(child.items(product) \
                                    for child in self._children))

    def __eq__(self, other):
        return isinstance(other, _CompositeRequest) \
            and self._children==other._children

    def __hash__(self): return hash(self._children)

    # def filter(self, product): raise NotImplementedError()
    # def filterout(self, product): raise NotImplementedError()


class LambdaRequest(Request):
    """The LambdaRequest is a Request that must initialized using a
    lambda function.
    """
    def __init__(self, test):
        super().__init__()
        self._func = assertIsInstance(test, collections.Callable)

    def test(self, product):
        return product is Offer.UNDEFINED or self._func(product)

    def items(self, product):
        return tuple() if not self.test(product) \
            else product.items() if isinstance(product, collections.Mapping) \
            else enumerate(product) if isinstance(product, collections.Sequence) \
            else ((k,v) for k,v in dict(product) if not k.startswith("_"))

    def __eq__(self, other):
        return isinstance(other, LambdaRequest) and self._func==other._func

    def __hash__(self): return hash(self._func)

    # def filter(self, product): raise NotImplementedError()
    # def filterout(self, product): raise NotImplementedError()

# -------------------------------------------------------------------
# Producer

from boing.core.observer import Observable, Observer

class Producer(Observable):

    demandChanged = QtCore.pyqtSignal()
    """Signal emitted when the aggregate demand changes."""

    offerChanged = QtCore.pyqtSignal()
    """Signal emitted when its own offer changes."""

    demandedOfferChanged = QtCore.pyqtSignal()
    """Signal emitted when its own demanded offer changes."""

    def __init__(self, offer, tags=None,
                 store=None, retrieve=None, haspending=None,
                 parent=None):
        """:class:`Producer` instances are :class:`Observable
        <boing.core.observer.Observable>` objects able to post products to
        a set of subscribed :class:`Consumer` instances. The argument
        *offer* must be an instance of :class:`Offer` and it define the
        products this producer will supply, while *tags* must be a dict or
        None. The argument *store* can be a callable object to be used as a
        handler for storing posted products (see :meth:`_store` for the
        handler arguments) or None, while *retrieve* can be a callable
        object to be used as a handler for retrieving stored products (see
        :meth:`_retrieveAndDeliver` for the handler arguments) or
        None. *parent* defines the consumer's parent.

        When a producer is demanded to posts a product, for each registered
        consumer it tests the product with the consumer’s request and only
        if the match is valid it triggers the consumer.
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
        self.__haspendingproducts = assertIsInstance(haspending,
                                                     None, collections.Callable)

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

    def hasPendingProducts(self, consumer=None):
        # Call custom function if defined, otherwise use default method.
        return self.__haspendingproducts(self, consumer) \
            if self.__haspendingproducts is not None \
            else self._defaultHasPendingProducts(consumer)

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

    def _defaultHasPendingProducts(self, consumer=None):
        if consumer is None:
            l = lambda record: hasattr(record, "products") and record.products
            rvalue = any(map(l, self._Observable__observers.values()))
        else:
            record = self._getRecord(consumer)
            rvalue = hasattr(record, "products") and bool(record.products)
        return rvalue

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

    @QtCore.pyqtSlot()
    def _refreshDemandedOffer(self):
        """Recalculate the demanded offer."""
        refresh = Offer(iter=filter(self._aggregatedemand.test, self.offer()))
        if self._demandedoffer!=refresh:
            self._demandedoffer = refresh
            self._activetags = set(tag for tag, request in self._tags.items() \
                                       if any(map(request.test,
                                                  self._demandedoffer)))
            self.demandedOfferChanged.emit()

    def addObserver(self, observer, mode=QtCore.Qt.QueuedConnection):
        rvalue = super().addObserver(observer, mode)
        if rvalue and isinstance(observer, Consumer):
            observer.requestChanged.connect(self._refreshAggregateDemand)
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
        elif isinstance(other, Consumer):
            # Subscribe current producers to the other's consumers
            it = other.consumers() if isinstance(other, Composite) else (other, )
            for cons in it:
                cons.subscribeTo(self)
            internals = (self, )+tuple(other.internals()) \
                if isinstance(other, Composite) else (self, other)
            if isinstance(other, Worker):
                producers = tuple(other.producers()) \
                    if isinstance(other, Composite) else (other, )
                rvalue = CompositeProducer(*producers, internals=internals)
            else:
                rvalue = Composite(*internals)
        else:
            rvalue = NotImplemented
        return rvalue

    def __radd__(self, other):
        return self if other is None else NotImplemented

    def __or__(self, other):
        if other is None:
            rvalue = self
        elif isinstance(other, Composite):
            # Let the Composite's '__ror__' method to be used
            rvalue = NotImplemented
        else:
            if isinstance(other, Worker):
                rvalue = CompositeWorker(consumers=(other, ),
                                         producers=(self, other))
            elif isinstance(other, Producer):
                rvalue = CompositeProducer(self, other)
            else:
                rvalue = NotImplemented
        return rvalue

    def __ror__(self, other):
        """Return the result of self|other, since | operator is
        commutative."""
        return self.__or__(other)

    def _debugData(self):
        rvalue = super()._debugData()
        rvalue["offer"] = self.offer()
        rvalue["demandedOffer"] = self.demandedOffer()
        rvalue["aggregateDemand"] = self.aggregateDemand()
        return rvalue

    class ConfigurableOffer:
        """The ConfigurableOffer class provides the method
        :meth:`setOffer`, which enables to set the offer of the
        producer.  Inherit both Producer and ConfigurableOffer to
        grant such behaviour, e.g.::

           class MyProducer(Producer, Producer.ConfigurableOffer):
               pass

        """
        def setOffer(self, offer):
            """Set *offer* as the new producer's offer."""
            if self._offer!=offer:
                self._offer = offer
                self.offerChanged.emit()

# -------------------------------------------------------------------
# Consumer

class Consumer(Observer):

    class _InternalQObject(Observer._InternalQObject):
        requestChanged = QtCore.pyqtSignal()

    @property
    def requestChanged(self):
        """Signal emitted when the new consumer's request changes."""
        return self._internal.requestChanged

    def __init__(self, request, consume=None, hz=None, parent=None):
        """:class:`Consumer` objects are :class:`Observer
        <boing.core.observer.Observer>` objects that can be subscribed
        to several :class:`Producer` instances for receiving their
        products. When a producer posts a product, it triggers the
        registered consumers; then the consumers will immediately or
        at regular time interval demand to the producer the new
        products.

        .. warning:: Many consumers can be subscribed to a single
           producer. Each new product is actually shared within the
           different consumers, therefore a consumer **MUST NOT**
           modify any received product, unless it is supposed to be
           the only consumer.

        Consumers have a :class:`Request`. When a producer is demanded
        to posts a product, it tests the product with the consumer's
        request and only if the match is valid it triggers the
        consumer.

        """
        super().__init__(hz=hz, parent=parent)
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
        """Consume the *products* posted from *producer*."""
        # Call custom function if defined, otherwise use default method.
        return self.__consume(self, products, producer) \
            if self.__consume is not None \
            else None

    def __add__(self, other):
        return self if other is None else NotImplemented

    def __radd__(self, other):
        return self if other is None else NotImplemented

    def __or__(self, other):
        if other is None:
            rvalue = self
        elif isinstance(other, Composite):
            # Let the Composite's '__ror__' method to be used
            rvalue = NotImplemented
        elif isinstance(other, Worker):
            rvalue = CompositeWorker((self, other), (other, ))
        elif isinstance(other, Consumer):
            rvalue = CompositeConsumer(self, other)
        else:
            rvalue = NotImplemented
        return rvalue

    def __ror__(self, other):
        """Return the result of self|other, since | operator is
        commutative."""
        return self.__or__(other)

    def _debugData(self):
        rvalue = super()._debugData()
        rvalue["request"] = self.request()
        return rvalue

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

# -------------------------------------------------------------------
# Request and offer propagation

class _PropagatingProducer(Producer):

    def __init__(self, consumer, offer, tags=None,
                 store=None, retrieve=None, haspending=None,
                 parent=None):
        """A :class:`_PropagatingProducer` is able to provide as result of
        the method :meth:`offer` its own *offer* added to the offers
        of all the producers subscribed to *consumer*.

        """
        super().__init__(offer, tags, store, retrieve, haspending, parent)
        self._cumulatedoffer = offer
        self.__cons = assertIsInstance(consumer, None, Consumer)
        if self.__cons is not None:
            self.__cons.observableAdded.connect(self.__followOffer)
            self.__cons.observableRemoved.connect(self.__unfollowOffer)

    def offer(self):
        """Return its own *offer* added to the offers of all the
        producers subscribed to :meth:`_consumer` if
        :meth:`isPropagatingOffer` is ``True``, otherwise its own
        offer."""
        return self._cumulatedoffer

    def isPropagatingOffer(self):
        """Return whether it is propagating the offer of a target
        :class:`Consumer`."""
        return True

    def _selfOffer(self):
        """Return its own offer."""
        return super().offer()

    def _consumer(self):
        """Return the consumer it is propagating the offer."""
        return self.__cons

    def _setConsumer(self, consumer):
        """Set the target consumer to *consumer*."""
        if self.__cons is not None:
            self.__cons.observableAdded.disconnect(self.__followOffer)
            self.__cons.observableRemoved.disconnect(self.__unfollowOffer)
        self.__cons = consumer
        self.__cons.observableAdded.connect(self.__followOffer)
        self.__cons.observableRemoved.connect(self.__unfollowOffer)

    def _propagateOffer(self):
        """Update the cumulated offer."""
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

    @QtCore.pyqtSlot(Observable)
    def __followOffer(self, observable):
        if isinstance(observable, Producer):
            # Observed consumer's offer influence self wise offer
            observable.offerChanged.connect(self._propagateOffer)
            self._propagateOffer()

    @QtCore.pyqtSlot(Observable)
    def __unfollowOffer(self, observable):
        if isinstance(observable, Producer):
            observable.offerChanged.disconnect(self._propagateOffer)
            self._propagateOffer()

    class ConfigurableOffer(Producer.ConfigurableOffer):
        def setOffer(self, offer):
            if self._offer!=offer:
                self._offer = offer
                self._propagateOffer()

class _PropagatingConsumer(Consumer):

    def __init__(self, producer, request, consume=None, hz=None, parent=None):
        """A :class:`_PropagatingConsumer` is able to provide as result of
        the method :meth:`request` its own *request* added to the requests
        of all the consumers subscribed to *producer*.

        """
        super().__init__(request, consume, hz, parent)
        self._cumulatedrequest = request
        self.__prod = assertIsInstance(producer, None, Producer)
        if self.__prod is not None:
            # demandedOffer and aggregateDemand influence the cumulated request
            self.__prod.demandedOfferChanged.connect(self._propagateRequest)
            self.__prod.demandChanged.connect(self._propagateRequest)
        self.requestChanged.connect(self._propagateRequest)

    def request(self):
        """Return its own request added to the requests of all the
        consumers subscribed to its associated producer."""
        return self._cumulatedrequest

    def isPropagatingRequest(self):
        """Return whether it is propagating the requests of the
        consumers subscribed to its associated producer."""
        return True

    def _selfRequest(self):
        return super().request()

    def _producer(self):
        """Return the producer is is associated to."""
        return self.__prod

    def _setProducer(self, producer):
        """Set the producer it is associated to to *producer*."""
        if self.__prod is not None:
            self.__prod.demandedOfferChanged.disconnect(self._propagateRequest)
            self.__prod.demandChanged.disconnect(self._propagateRequest)
        self.__prod = producer
        self.__prod.demandedOfferChanged.connect(self._propagateRequest)
        self.__prod.demandChanged.connect(self._propagateRequest)

    def _propagateRequest(self):
        """Refresh the cumulated request."""
        updated = self._selfRequest()
        if self.isPropagatingRequest() and self._producer() is not None:
            updated += self._producer().aggregateDemand()
        if self.request()!=updated:
            self._cumulatedrequest = updated
            self.requestChanged.emit()

    class ConfigurableRequest(Consumer.ConfigurableRequest):
        def setRequest(self, request):
            """Set *request* as the consumer's request."""
            if self._request!=request:
                self._request = assertIsInstance(request, Request)
                self._propagateRequest()

# -------------------------------------------------------------------
# Worker

class Worker:
    """A :class:`Worker` instance is both a :class:`Producer` and a
    :class:`Consumer`. The class :class:`Worker` is by itself an
    abstract class. Consider using the concrete class
    :class:`BaseWorker` instead.

    """
    def __init__(self): raise NotImplementedError()


class BaseWorker(_PropagatingProducer, _PropagatingConsumer, Worker):

    def __init__(self, request, offer,
                 tags=None, store=None, retrieve=None, haspending=None,
                 consume=None, hz=None, parent=None):
        """A :class:`BaseWorker` is the simplest concrete
        :class:`Worker`. By default it does nothing with the products
        it receives, but it is able to propagate the offers of the
        producers it is subscribed to, and it is able to propagate the
        requests of the consumers that are subscribed to it.

        """
        _PropagatingProducer.__init__(self, None, offer, tags,
                                      store, retrieve, haspending, parent)
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
        elif isinstance(other, Consumer):
            # Subscribe current producers to the other's consumers
            it = other.consumers() if isinstance(other, Composite) else (other, )
            for cons in it:
                cons.subscribeTo(self)
            internals = (self, )+tuple(other.internals()) \
                if isinstance(other, Composite) else (self, other)
            if isinstance(other, Worker):
                producers = tuple(other.producers()) \
                    if isinstance(other, Composite) else (other, )
                rvalue = CompositeWorker((self, ), producers, internals=internals)
            else:
                rvalue = CompositeConsumer(self, internals=internals)
        else:
            rvalue = NotImplemented
        return rvalue

    def __or__(self, other):
        if other is None:
            rvalue = self
        elif isinstance(other, Composite):
            # Let the Composite '__ror__' method be used
            rvalue = NotImplemented
        elif isinstance(other, Producer) or isinstance(other, Consumer):
            consumers = (self, other) if isinstance(other, Consumer) else (self, )
            producers = (self, other) if isinstance(other, Producer) else (self, )
            rvalue = CompositeWorker(consumers, producers)
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


class NopWorker(BaseWorker):

    def __init__(self, store=None, retrieve=None, hz=None, parent=None):
        """:class:`NopWorker` instances simply forwards all the
        products they receive.

        """
        super().__init__(request=Request.NONE, offer=Offer(),
                         store=store, retrieve=retrieve, hz=hz, parent=parent)

    def _consume(self, products, producer):
        """Forward all the products it has been received."""
        for product in products:
            self.postProduct(product)

# -------------------------------------------------------------------
# WiseWorker

class WiseWorker(BaseWorker):

    def __init__(self, request, offer, **kwargs):
        """A :class:`WiseWorker` instance is able to automatically
        detect whenever it should not propose its own offer or its own
        request; this is done in order to save computational time.
        The behaviour of :class:`WiseWorker` objects works as follows:

        1. Its own request is deactivated if there is no consumer
           insterested to its offer (i.e. no items in demandedoffer),
           which means: <<If nobody is interested to its products, why
           should it requires the products necessary to the
           processing?>>.

        2. Its own offer is deactivated if there is no producer that
           meets its request, which means: <<If nobody can provide it
           the products it requires for processing, how can it propose
           its offer?>>.

        A :class:`WiseWorker` is active (see method :meth:`isActive`)
        when its own request is not deactivated (i.e. case 1).

        A :class:`WiseWorker` can be forced to be activated or
        deactivated. Use the method :meth:`setForcing` to impose a
        specific behaviour.

        Use :const:`WiseWorker.TUNNELING` as the worker Offer, when the
        worker is supposed to process and then forward a subset of the
        products it receives. This is necessary since sometimes it may
        be possible that the worker cannot have a predefined offer
        since it always depend from the offer of the observed
        producers.

        """
        self._tunneling = offer is WiseWorker.TUNNELING
        super().__init__(request,
                         Offer() if offer is WiseWorker.TUNNELING else offer,
                         **kwargs)
        self._active = False
        self._forced = None

    def isActive(self):
        """The :class:`WiseWorker` is active only if its offer is
        requested from any subscribed consumer, unless it is forced
        (see :meth:`forcing`)."""
        return self._active

    def isTunneling(self):
        """Return True if the worker is forwarding a subset of the
        products it receives."""
        return self._tunneling

    def forcing(self):
        """Return whether the WiseWorker is being forced. Return a
        value within (:const:`WiseWorker.ACTIVATED`,
        :const:`WiseWorker.DEACTIVATED`, :const:`WiseWorker.NONE`)."""
        return self._forced

    def setForcing(self, forcing):
        """Impose to the :class:`WiseWorker` to be activated,
        deactivated or remove a previous forcing. *forcing* must be a
        value within (:const:`WiseWorker.ACTIVATED`,
        :const:`WiseWorker.DEACTIVATED`, :const:`WiseWorker.NONE`)."""
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
        elif self.forcing() is WiseWorker.DEACTIVATED:
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

    class _Forcing: pass
    ACTIVATED = _Forcing()
    """Value used to force the :class:`WiseWorker` to be activated."""
    DEACTIVATED = _Forcing()
    """Value used to force the :class:`WiseWorker` to be
    deactivated."""
    NONE = _Forcing()
    """Value used to let the :class:`WiseWorker` decide it it should
    be active."""

    TUNNELING = object()
    """Value used to set the :class:`WiseWorker` the tunneling
    mode."""

# -------------------------------------------------------------------
# Functor

class Functor(WiseWorker):

    def __init__(self, args, offer, blender, process=None, **kwargs):
        """The :class:`Functor` class is practical base class for
        inheriting custom processing :class:`Workers`. Instead of
        implementing the classic :meth:`Consumer._consume` method, the
        :class:`Functor` proposes the more powerfull method
        :meth:`_process`. This handler method receives as argument
        *sequence*, an iterator over the operands, which are iterators
        over the couples (key, value) obtained from applying the
        method :meth:`Request.items` of the request of the functor on
        the list of received products. This enables to access directly
        to the name and values of the required data without the need
        of reimplementing the code to get them. The method
        :meth:`_process` is a generator method and it it supposed to
        yield the the couples (key, value) representing the result of
        the node processing. The yielded results are automatically
        considered by the functor to create a new product that will be
        automatically posted.

        The functor uses a :class:`Functor.Blender` object to create
        the new product. A set of predefined blenders are used to set
        the functor behaviour:

        - :const:`Functor.MERGE` --- Join the original product and
          results of the functor.

        - :const:`Functor.MERGECOPY` --- Make a deep copy of the
          original product and then join the results of the functor.

        - :const:`Functor.RESULTONLY` --- Post as product only the
          result of the functor.

        A :class:`Functor` instance propagates the requests only if
        the current blender is a :class:`MergeBlender` and it
        propagates the offers only if the current blender is a
        :class:`MergeBlender` or if it is tunneling (see
        :meth:`WiseWorker.isTunneling`).

        """
        super().__init__(request=args, offer=offer, **kwargs)
        self._blender = assertIsInstance(blender, Functor.Blender)
        self.__process = assertIsInstance(process, None, collections.Callable)

    def blender(self):
        """Return the current active :class:`Functor.Blender`."""
        return self._blender

    def _consume(self, products, producer):
        results = tuple() if not self.isActive() \
            else self._process(map(self._selfRequest().items, products),
                               producer)
        products = self.blender().blend(products,
                                        results if results is not None else tuple())
        for product in filter(None, products):
            self.postProduct(product)

    def _process(self, sequence, producer):
        """This handler method receives as argument *sequence*, an
        iterator over the operands, which are iterators over the couples
        (key, value) obtained from applying the method
        :meth:`Request.items` of the request of the functor on the
        list of received products. This enables to access directly to
        the name and values of the required data without the need of
        reimplementing the code to get them. This is a generator
        method and it it supposed to yield the the couples (key,
        value) representing the result of the node processing."""
        if self.__process is not None:
            return self.__process(sequence, producer)
        else:
            raise NotImplementedError()

    def isPropagatingRequest(self):
        """Return whether it is propagating the requests of the
        consumers subscribed to its associated producer."""
        return isinstance(self.blender(), Functor.MergeBlender)

    def isPropagatingOffer(self):
        """Return whether it is propagating the offer of a target
        :class:`Consumer`."""
        return self.isTunneling() \
            or isinstance(self.blender(), Functor.MergeBlender)

    def _debugData(self):
        rvalue = super()._debugData()
        rvalue["blender"] = self.blender()
        return rvalue

    class Blender(metaclass=abc.ABCMeta):
        @abc.abstractmethod
        def blend(self, products, results):
            raise NotImplementedError()

    class MergeBlender(Blender):
        def __repr__(self): return "Blender.MERGE"

    class ResultOnlyBlender(Blender):
        def __repr__(self): return "Blender.RESULTONLY"

# -------------------------------------------------------------------
# Composites

class _ForwardingConsumer(_PropagatingConsumer):
    """A :class:`_ForwardingConsumer` is a
    :class:`_PropagatingConsumer` that requires its associated
    producer to forward all the products it receives.

    """
    def _consume(self, products, producer):
        if self._producer() is not None:
            for product in products:
                self._producer().postProduct(product)


class Composite(QtCore.QObject):

    def __init__(self, *internals, parent=None):
        """A :class:`Composite` instance stores a set of internal
        objects using strong references.

        Use the method :meth:`internals` to scroll the references
        objects.

        """
        # This trick is necessary since PyQt's QObjects cannot use
        # multiple inheritance
        if not sip.ispycreated(self): QtCore.QObject.__init__(self, parent)
        self.__internals = set(internals)

    def internals(self):
        """Return an iterator over the set of internal nodes for which
        a strong reference is stored."""
        return iter(self.__internals)

    def debug(self, fd=sys.stdout, maxdepth=1, grapher=None):
        if grapher is None: grapher = SimpleGrapher()
        grapher.draw(self, file=fd, maxdepth=maxdepth, memo=set())

    def _debugData(self): return collections.OrderedDict()

    def _debugSiblings(self):
        return collections.OrderedDict(internals=self.internals())


class CompositeProducer(_PropagatingProducer, Composite):

    def __init__(self, *producers, internals=set(), parent=None):
        """A :class:`CompositeProducer` combines in parallel the list
        of *producers* so that they can be considered as a single
        :class:`Producer`. The argument *internals* can be used to
        specify the object for which a strong reference should be
        kept. All *producers* are by default added as internals of the
        :class:`Composite`.

        """
        _PropagatingProducer.__init__(
            self, _ForwardingConsumer(None, Request.NONE),
            offer=Offer(), parent=parent)
        Composite.__init__(self, *(set(producers).union(set(internals))))
        self._consumer()._setProducer(weakref.proxy(self))
        for prod in producers:
            assertIsInstance(prod, Producer)
            self._consumer().subscribeTo(prod)

    def producers(self):
        """Return an iterator over the first level producers."""
        return self._consumer().observed()

    def __add__(self, other):
        if other is None:
            rvalue = self
        elif isinstance(other, Consumer):
            # Subscribe current producers to the other's consumers
            it = itertools.product(self.producers(), other.consumers()) \
                if isinstance(other, Composite) \
                else zip(self.producers(), itertools.repeat(other))
            for prod, cons in it:
                cons.subscribeTo(prod)
            internals = tuple(self.internals())+tuple(other.internals()) \
                if isinstance(other, Composite) \
                else tuple(self.internals())+(other, )
            if isinstance(other, Worker):
                producers = tuple(other.producers()) \
                    if isinstance(other, Composite) else (other, )
                rvalue = CompositeProducer(*producers, internals=internals)
            else:
                rvalue = Composite(*internals)
        else:
            rvalue = NotImplemented
        return rvalue

    def __or__(self, other):
        if other is None:
            rvalue = self
        elif isinstance(other, Producer):
            producers = tuple(self.producers())+tuple(other.producers()) \
                if isinstance(other, Composite) \
                else tuple(self.producers())+(other, )
            internals = tuple(self.internals())+tuple(other.internals()) \
                if isinstance(other, Composite) else self.internals()
            if isinstance(other, Worker):
                consumers = tuple(other.consumers()) \
                    if isinstance(other, Composite) else (other, )
                rvalue = CompositeWorker(consumers, producers, internals)
            else:
                rvalue = CompositeProducer(*producers, internals=internals)
        else:
            rvalue = NotImplemented
        return rvalue

    def _debugSiblings(self):
        rvalue = super()._debugSiblings()
        rvalue.update(consumer=self._consumer())
        rvalue.move_to_end('consumer', last=False)
        return rvalue


class CompositeConsumer(_ForwardingConsumer, Composite):

    def __init__(self, *consumers, internals=set(), parent=None):
        """A :class:`CompositeConsumer` combines in parallel the list
        of *consumers* so that they can be considered as a single
        :class:`Consumer`. The argument *internals* can be used to
        specify the object for which a strong reference should be
        kept. All *consumers* are by default added as internals of the
        :class:`Composite`.

        """
        _ForwardingConsumer.__init__(
            self, _PropagatingProducer(None, Offer()),
            Request.NONE, parent=parent)
        Composite.__init__(self, *(set(consumers).union(set(internals))))
        self._producer()._setConsumer(weakref.proxy(self))
        for cons in consumers:
            assertIsInstance(cons, Consumer)
            self._producer().addObserver(cons)

    def consumers(self):
        """Return an iterator over the first level consumers."""
        return self._producer().observers()

    def __add__(self, other):
        return self if other is None else NotImplemented

    def __or__(self, other):
        if other is None:
            rvalue = self
        elif isinstance(other, Consumer):
            consumers = tuple(self.consumers())+tuple(other.consumers()) \
                if isinstance(other, Composite) \
                else tuple(self.consumers())+(other, )
            internals = tuple(self.internals())+tuple(other.internals()) \
                if isinstance(other, Composite) else self.internals()
            if isinstance(other, Worker):
                producers = tuple(other.producers()) \
                    if isinstance(other, Composite) else (other, )
                rvalue = CompositeWorker(consumers, producers, internals)
            else:
                rvalue = CompositeConsumer(*consumers, internals=internals)
        else:
            rvalue = NotImplemented
        return rvalue

    def _debugSiblings(self):
        rvalue = super()._debugSiblings()
        rvalue.update(producer=self._producer())
        rvalue.move_to_end('producer', last=False)
        return rvalue


class CompositeWorker(CompositeProducer, CompositeConsumer, Worker):

    def __init__(self, consumers, producers, internals=set(), parent=None):
        """A :class:`CompositeWorker` object combines in parallel the
        list of *producers* and in parallel the list of *consumers* so
        that they can be considered as a single :class:`Worker`. The
        argument *internals* can be used to specify the object for
        which a strong reference should be kept. All *producers* and
        *consumers* are by default added as internals of the
        :class:`Composite`.

        """
        internals = set(tuple(consumers)+tuple(producers)+tuple(internals))
        CompositeProducer.__init__(self, *producers, internals=internals,
                                   parent=parent)
        CompositeConsumer.__init__(self, *consumers, internals=internals)

    def __del__(self):
        CompositeProducer.__del__(self)
        CompositeConsumer.__del__(self)

    def _checkRefs(self):
        CompositeProducer._checkRefs(self)
        CompositeConsumer._checkRefs(self)

    def clear(self):
        CompositeProducer.clear(self)
        CompositeConsumer.clear(self)

    def __add__(self, other):
        if other is None:
            rvalue = self
        elif isinstance(other, Consumer):
            # Subscribe current producers to the other's consumers
            it = itertools.product(self.producers(), other.consumers()) \
                if isinstance(other, Composite) \
                else zip(self.producers(), itertools.repeat(other))
            for prod, cons in it:
                cons.subscribeTo(prod)
            internals = tuple(self.internals())+tuple(other.internals()) \
                if isinstance(other, Composite) \
                else tuple(self.internals())+(other, )
            if isinstance(other, Worker):
                producers = tuple(other.producers()) \
                    if isinstance(other, Composite) else (other, )
                rvalue = CompositeWorker(tuple(self.consumers()),
                                         producers, internals)
            else:
                rvalue = CompositeConsumer(*self.consumers(),
                                            internals=internals)
        else:
            rvalue = NotImplemented
        return rvalue

    def __or__(self, other):
        if other is None:
            rvalue = self
        elif isinstance(other, Producer) or isinstance(other, Consumer):
            consumers = tuple(self.consumers()) + tuple(other.consumers()) \
                if isinstance(other, CompositeConsumer) \
                else tuple(self.consumers()) + (other, ) \
                if isinstance(other, Consumer) \
                else tuple(self.consumers())
            producers = tuple(self.producers()) + tuple(other.producers()) \
                if isinstance(other, CompositeProducer) \
                else tuple(self.producers()) + (other, ) \
                if isinstance(other, Producer) \
                else tuple(self.producers())
            internals = tuple(self.internals())+tuple(other.internals()) \
                if isinstance(other, Composite) \
                else self.internals()
            rvalue = CompositeWorker(consumers, producers, internals)
        else:
            rvalue = NotImplemented
        return rvalue

    def _debugData(self):
        rvalue = CompositeConsumer._debugData(self)
        rvalue.update(CompositeProducer._debugData(self))
        return rvalue

    def _debugSiblings(self):
        rvalue = CompositeConsumer._debugSiblings(self)
        rvalue.update(CompositeProducer._debugSiblings(self))
        return rvalue
