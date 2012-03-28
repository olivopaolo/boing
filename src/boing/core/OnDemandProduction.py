# -*- coding: utf-8 -*-
#
# boing/core/OnDemandProduction.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import weakref

from PyQt4 import QtCore

from boing.core.ProducerConsumer import Producer, Consumer

class OnDemandProducer(Producer):
    """OnDemandProducers filter the posted products with respect to
    consumers' request, if any. Each subscribed consumer is its own
    pending products and a trigger signal, which is used to notify the
    new products."""
    
    class ConsumerRecord(QtCore.QObject):
        trigger = QtCore.pyqtSignal(QtCore.QObject)
        def __init__(self, consumer):
            QtCore.QObject.__init__(self)
            self.request = consumer.request() \
                if isinstance(consumer, SelectiveConsumer) \
                else OnDemandProducer.ANY_PRODUCT
            self.products = None
            self.notified = False

    """Any product request tag."""
    ANY_PRODUCT = "*"
    """Emitted when a SelectiveConsumer is added, removed or its
    request has changed."""
    demandChanged = QtCore.pyqtSignal()

    def __init__(self, productoffer=None, 
                 cumulate=None, test=None, parent=None):
        Producer.__init__(self, parent)
        self._productoffer = productoffer
        self._consumers = dict()
        self.cumulate = cumulate if isinstance(cumulate, collections.Callable) \
            else lambda s, p: [p] if s is None else s + [p]
        self.test = test if isinstance(test, collections.Callable) \
            else lambda request, product: True

    def __del__(self):        
        for ref, record in self._consumers.items():
            if ref() is not None: record.trigger.disconnect(ref()._react)
        Producer.__del__(self)

    def _checkRef(self):
        Producer._checkRef(self)
        # Keep only alive references
        old = len(self._consumers)
        self._consumers = dict((ref, record) \
                                   for ref, record in self._consumers.items() \
                                   if ref() is not None)
        if old!=len(self._consumers):
            self.demandChanged.emit()
    
    def addObserver(self, reactiveobject, mode=QtCore.Qt.QueuedConnection): 
        rvalue = Producer.addObserver(self, reactiveobject)
        if rvalue and isinstance(reactiveobject, Consumer):
            record = OnDemandProducer.ConsumerRecord(reactiveobject)
            record.trigger.connect(reactiveobject._react, mode)
            self._consumers[weakref.ref(reactiveobject)] = record
            self.demandChanged.emit()
        return rvalue

    def removeObserver(self, reactiveobject):
        rvalue = Producer.removeObserver(self, reactiveobject)
        if rvalue:
            for ref, record in self._consumers.items():
                if ref() is reactiveobject: 
                    record.trigger.disconnect(reactiveobject._react)
                    del self._consumers[ref]
                    self.demandChanged.emit()
                    break
        return rvalue
    
    def clearObservers(self):
        for ref, record in self._consumers.items():
            record.trigger.disconnect(ref()._react)
        self._consumers.clear()
        Producer.clearObservers(self)
        self.demandChanged.emit()

    def productOffer(self):
        return self._productoffer

    def isRequested(self, product):
        """A product is requested if any of the subscribed consumers
        requires it."""
        for record in self._consumers.values():
             if self.test(record.request, product): rvalue = True ; break
        return rvalue

    def _postProduct(self, product):
        for ref, record in self._consumers.items():
            self._postProductToRecord(product, ref(), record)

    def _postProductTo(self, product, consumer):
        """Posts a product to a target currently subscribed consumer;
        it returns True if the consumer is interested to the product
        or False if the product is not requested. Raises Exception if
        'consumer' is not a currently subscribed consumer."""
        for ref, record in self._consumers.items():
            if ref()==consumer:
                return self._postProductToRecord(product, consumer, record)
        else:
            raise Exception(
                "Cannot post a product to un unsubscribed consumer: %s"%consumer)

    def _postProductToRecord(self, product, consumer, record):
        rvalue = self.test(record.request, product)
        if rvalue:
            record.products = self.cumulate(record.products, product)
            if record.products and not record.notified: 
                record.notified = True
                record.trigger.emit(self)
        return rvalue

    def products(self, customer=None):
        rvalue = None
        for ref, record in self._consumers.items():
            if ref() is customer:
                record.notified = False                
                rvalue = record.products
                record.products = None
                break
        else:
            raise Exception(
                "Unsubscribed consumers cannot get products: %s"%customer)
        return rvalue

    def _requestChange(self, consumer, request):
        """Invoked by a SelectiveConsumer to notify that its request
        is changed (since SelectiveConsumer is not a QObject)."""
        for ref, record in self._consumers.items():
            if ref() is consumer: 
                record.request = request
                self.demandChanged.emit()
                break


class SelectiveConsumer(Consumer):
    """The SelectiveConsumer has some request that a Producer
    may use to filter products production or storing. It is not
    guaranteed that only requested products are provided to the
    SelectiveConsumer."""

    def __init__(self, request=OnDemandProducer.ANY_PRODUCT, hz=None):
        Consumer.__init__(self, hz)
        self.__request = request

    def request(self):
        return self.__request

    def setRequest(self, request):
        """Set the new product request."""
        if request!=self.__request:
            self.__request = request
            # Notify all OnDemandProducers it is subscribed to
            for observable in self.observed():
                if isinstance(observable, OnDemandProducer):
                    observable._requestChange(self, self.__request)

# -------------------------------------------------------------------

if __name__ == '__main__':
    import signal
    import sys
    if len(sys.argv)<2 or not sys.argv[1].isdecimal():
        print("usage: %s <seconds>"%sys.argv[0])
        sys.exit(1)
    class DebugConsumer(SelectiveConsumer):
        def _consume(self, products, producer):
            print("Consumer", self.request(), "obtained [",
                  ", ".join((str(p) for p in products)), "]")
    def production(producer, product):
        return lambda : producer._postProduct(product)
    # Init app
    app = QtCore.QCoreApplication(sys.argv)
    signal.signal(signal.SIGINT, lambda *args: app.quit())
    QtCore.QTimer.singleShot(int(sys.argv[1])*1000, app.quit)
    # Init producer
    test = lambda request, product: product in request
    prod = OnDemandProducer({"statue", "painting", "obelisk", "temple"}, 
                            test=test)
    for product, period in zip(prod.productOffer(), (400, 500, 800, 900)):
        f = production(prod, product)
        tid = QtCore.QTimer(prod)
        tid.timeout.connect(f)
        tid.start(period)
    # Init consumers
    cons1 = DebugConsumer(("statue", "painting"))
    cons1.subscribeTo(prod)
    cons2 = DebugConsumer(("painting", "temple"), 1)
    cons2.subscribeTo(prod)
    # Run
    sys.exit(app.exec_())
