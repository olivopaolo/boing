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

from PyQt4.QtCore import QObject, pyqtSignal, Qt

from boing.eventloop.ProducerConsumer import AbstractProducer, Consumer
from boing.eventloop.ReactiveObject import Observable

class ConsumerRecord(QObject):
    
    trigger = pyqtSignal(QObject)

    def __init__(self):
        QObject.__init__(self)
        self.products = None
        self.notified = False


class OnDemandProducer(AbstractProducer):
    """OnDemandProducers filter the posted products with respect to
    consumers' restrictions, if any. Each subscribed consumer is
    associated to a list to store pending products and a trigger
    signal, which is used to notify the new products."""

    def __init__(self, cumulate=None, match=None, parent=None):
        AbstractProducer.__init__(self, parent)
        self._consumers = {}
        self.cumulate = cumulate if isinstance(cumulate, collections.Callable) \
            else lambda p, s: [p] if s is None else s + [p]
        self.match = match if isinstance(match, collections.Callable) \
            else lambda *args: True
    
    def addObserver(self, observer, mode=Qt.QueuedConnection):
        if AbstractProducer.addObserver(self, observer):
            record = ConsumerRecord()
            record.trigger.connect(observer._react, mode)
            self._consumers[weakref.ref(observer)] = record
            return True
        else: return False

    def removeObserver(self, observer):
        if AbstractProducer.removeObserver(self, observer):
            for ref in self._consumers.keys():
                if ref() is observer:
                    del self._consumers[ref]
                    break
            return True
        else: return False

    def products(self, consumer):
        for ref, record in self._consumers.items():
            if ref() is consumer:
                record.notified = False
                products = record.products
                record.products = None
                return products
        else: return None

    def _postProduct(self, product):
        for ref, record in self._consumers.items():
            consumer = ref()
            subset = product if not hasattr(consumer, "restrictions") \
                else self.match(product, consumer.restrictions()) 
            if subset:
                record.products = self.cumulate(subset, record.products)
                if record.products and not record.notified: 
                    record.notified = True
                    record.trigger.emit(self)

    def _checkRef(self):
        AbstractProducer._checkRef(self)
        # Keep only alive references
        self._consumers = dict((ref,value) for ref,value in self._consumers.items() \
                                          if ref() is not None)


class SelectiveConsumer(Consumer):
    """The SelectiveConsumer has a tuple of requests that a Producer
    may used to filter products production or storing. It is not
    guaranteed that only requested products are provided to the
    SelectiveConsumer."""
   
    def __init__(self, restrictions=None, hz=None):
        """The argument 'restrictions' must be a tuple or None."""
        Consumer.__init__(self, hz)
        if restrictions is not None and not isinstance(restrictions, tuple): 
            raise ValueError("restrictions must be tuple or None, not %s"%
                             restrictions.__class__.__name__)
        self.__restrictions = restrictions

    def restrictions(self):
        return self.__restrictions


class DumpConsumer(SelectiveConsumer):

    def __init__(self, restrictions=None, hz=None, dumpsrc=False, dumpdest=False):
        SelectiveConsumer.__init__(self, restrictions, hz)
        self.dumpsrc = dumpsrc
        self.dumpdest = dumpdest

    def _consume(self, products, producer):
        if self.dumpsrc: print("from:", str(producer))
        if self.dumpdest: print("to:  ", str(self))
        for p in products:
            print(str(p))
        print()

# -------------------------------------------------------------------

if __name__ == '__main__':
    from boing.eventloop.EventLoop import EventLoop
    class DebugConsumer(SelectiveConsumer):
        def _consume(self, products, producer):
            print("Consumer", self.restrictions(), "obtained [",
                  ", ".join((str(p) for p in products)), "]")
    def produce(tid, producer, product):
        producer._postProduct(product)
    def match(product, request):
        return product if product in request else None
    # init producer
    prod = OnDemandProducer(match=match)
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
