# -*- coding: utf-8 -*-
#
# boing/eventloop/OnDemandProduction.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import weakref

from PyQt4 import QtCore

from boing.eventloop.ProducerConsumer import AbstractProducer, Consumer
from boing.eventloop.ReactiveObject import Observable

class OnDemandProducer(AbstractProducer):
    """OnDemandProducers filter the posted products with respect to
    consumers' requests, if any. Each subscribed consumer is
    associated to a list to store pending products and a trigger
    signal, which is used to notify the new products."""
    
    ANY_PRODUCT = ".*"

    class ConsumerRecord(QtCore.QObject):
    
        trigger = QtCore.pyqtSignal(QtCore.QObject)

        def __init__(self, requests):
            QtCore.QObject.__init__(self)
            self.products = None
            self.requests = requests
            self.notified = False

    def __init__(self, productoffer=None, cumulate=None, filter_=None, parent=None):
        """
        Set 'productoffer' to define the kind of objects this instance
        can produce.

        Set 'cumulate' to define a specific callable function used to cumulate 
        products.

        Set 'filter_' to define a specific callable function used to filter the 
        posted products for each registered consumers requirements.
        """
        AbstractProducer.__init__(self, parent)
        self._consumers = dict()
        self._productoffer = productoffer
        self.cumulate = cumulate if isinstance(cumulate, collections.Callable) \
            else lambda p, s: [p] if s is None else s + [p]
        self.filter = filter_ if isinstance(filter_, collections.Callable) \
            else lambda product, requests: product

    def __del__(self):        
        for ref, record in self._consumers.items():            
            record.trigger.disconnect(ref()._react)
        AbstractProducer.__del__(self)
    
    def addObserver(self, observer, mode=QtCore.Qt.QueuedConnection, 
                    requests=ANY_PRODUCT):
        rvalue = AbstractProducer.addObserver(self, observer)
        if rvalue:
            record = OnDemandProducer.ConsumerRecord(requests)
            record.trigger.connect(observer._react, mode)
            self._consumers[weakref.ref(observer)] = record
        return rvalue

    def removeObserver(self, observer):
        rvalue = AbstractProducer.removeObserver(self, observer)
        if rvalue:
            for ref, record in self._consumers.values():
                if ref() is observer: 
                    record.trigger.disconnect(observer._react)
                    del self._consumers[ref] ; break
        return rvalue

    def clearObservers(self):
        AbstractProducer.clearObservers(self)
        for ref, record in self._consumers.items():
            record.trigger.disconnect(ref()._react)
        self._consumers.clear()        

    def productOffer(self):
        return self._productoffer

    def overallDemand(self):
        """Return the union of all requests of the registered consumers."""
        raise NotImplementedError()

    def products(self, consumer):
        products = None
        for ref, record in self._consumers.items():
            if ref() is consumer:
                record.notified = False
                products = record.products
                record.products = None
                break
        return products

    def _postProduct(self, product):
        for ref, record in self._consumers.items():
            consumer = ref()
            subset = self.filter(product, record.requests) 
            if subset is not None:
                record.products = self.cumulate(subset, record.products)
                if record.products and not record.notified: 
                    record.notified = True
                    record.trigger.emit(self)

    def _checkRef(self):
        AbstractProducer._checkRef(self)
        # Keep only alive references
        self._consumers = dict((ref, value) \
                                   for ref, value in self._consumers.items() \
                                   if ref() is not None)


class SelectiveConsumer(Consumer):
    """The SelectiveConsumer has some requests that a Producer
    may used to filter products production or storing. It is not
    guaranteed that only requested products are provided to the
    SelectiveConsumer."""

    def __init__(self, requests=OnDemandProducer.ANY_PRODUCT, hz=None):
        Consumer.__init__(self, hz)
        self._requests = requests

    def requests(self):
        return self._requests

    def subscribeTo(self, observable, **kwargs):
        """Accepts argument 'requests' also."""
        req = self._requests
        for key, value in kwargs.items():
            if key=="requests": req = value
            else: raise TypeError(
                "subscribeTo() got an unexpected keyword argument '%s'"%
                key)
        if isinstance(observable, OnDemandProducer):
            return observable.addObserver(self, requests=req)
        else:
            return Consumer.subscribeTo(self, observable) 


class DumpConsumer(SelectiveConsumer, QtCore.QObject):

    def __init__(self, dumpsrc=False, dumpdest=False, count=False, 
                 parent=None, **kwargs):
        SelectiveConsumer.__init__(self, **kwargs)
        QtCore.QObject.__init__(self, parent)
        self.dumpsrc = dumpsrc
        self.dumpdest = dumpdest
        self.count = 0 if count else None

    def _consume(self, products, producer):
        if self.dumpsrc: print("from:", str(producer))
        if self.dumpdest: print("to:  ", str(self))
        for p in products:
            if self.count is not None:
                self.count += 1
                print("%d: %s"%(self.count, str(p)))
            else: print(str(p))
        print()

# -------------------------------------------------------------------

if __name__ == '__main__':
    from boing.eventloop.EventLoop import EventLoop
    class DebugConsumer(SelectiveConsumer):
        def _consume(self, products, producer):
            print("Consumer", self.requests(), "obtained [",
                  ", ".join((str(p) for p in products)), "]")
    def produce(tid, producer, product):
        producer._postProduct(product)
    def filter_(product, request):
        return product if product in request else None
    # init producer
    prod = OnDemandProducer(
        productoffer={"statue", "painting", "obelisk", "temple"},
        filter_=filter_)
    EventLoop.repeat_every(0.4, produce, prod, "statue")
    EventLoop.repeat_every(0.5, produce, prod, "painting")
    EventLoop.repeat_every(0.8, produce, prod, "obelisk")
    EventLoop.repeat_every(0.9, produce, prod, "temple")
    # init consumers
    cons1 = DebugConsumer(("statue", "painting"))
    cons1.subscribeTo(prod)
    cons2 = DebugConsumer(("painting", "temple"), 1)
    cons2.subscribeTo(prod)
    # run
    EventLoop.runFor(5)
    del prod, cons1, cons2
