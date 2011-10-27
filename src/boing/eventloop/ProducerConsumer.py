# -*- coding: utf-8 -*-
#
# boing/eventloop/ProducerConsumer.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import weakref

from boing.eventloop.ReactiveObject import Observable, DelayedReactive

class Producer(Observable) :
    """This Observable sends a notification each time it has a new
    product. Products can be obtained using the method products().
    Products are kept until all the registered ReactiveObjects
    have taken the pending products."""
    def __init__(self, parent=None):
        super().__init__(parent)
        """List of the pending products."""
        self._products = []
        """Store the index of the last product sent to each reactiveobject,
        so that the same products are not sent twice and it is possible
        to know when event can be removed (see self.__cleanup()).
        self.__history[ReactiveObject] = int """
        self.__history = {}

    def addObserver(self, observer):
        if super().addObserver(observer):
            self.__history.setdefault(weakref.ref(observer), 0)
            return True
        else: return False
        
    def removeObserver(self, observer):
        if super().removeObserver(observer):
            for ref in self.__history.keys():
                if ref() is observer:
                    del self.__history[ref]
                    self.__cleanup()
                    break
            return True
        else: return False

    def products(self, reactiveobject=None):
        """Return the list of the new products. If reactiveobject is
        None then the entire list is returned, otherwise only the new
        products are insered.  The argument reactiveobject is
        necessary to know when a product has been taken by all the
        registered ReactiveObjects."""
        if len(self._products)==0: return []
        else:
            if reactiveobject is None: return tuple(self._products)
            else:
                for ref, value in self.__history.items():
                    if ref() is reactiveobject:
                        products = self._products[value:] 
                        self.__history[ref] = len(self._products)
                        self.__cleanup() 
                        break
                else: products = tuple(self._products)
                return products

    def _postProduct(self, product):
        """Add a new product and notify it."""
        if len(self.observers()) > 0:
            self._products.append(product)
            self.notifyObservers()

    def __cleanup(self):
        """Remove the products that have been sent to all the
        observers."""
        if not self.__history: self._products = []
        else:
            min_ = min(self.__history.values())
            if min_ > 0:
                del self._products[:min_]
                for key in self.__history.keys():
                    self.__history[key] -= min_

    def _checkRef(self):
        super()._checkRef()
        # Keep only alive references
        self.__history = dict((ref,value) for (ref,value) in self.__history.items() \
                                          if ref() is not None)

class Consumer(DelayedReactive):
    """ReactiveObject that supports product consuming."""
    def __init__(self, hz=None, parent=None):
        super().__init__(hz, parent)

    def _refresh(self):
        for producer in self.queue():
            self._consume(producer.products(self), producer)

    def _consume(self, products, producer):
        """It can be overridden to define business logic, but do not invoke it
        directly."""
        pass

class DumpConsumer(Consumer):

    def __init__(self, hz=None, dumpsrc=False, dumpdest=False, parent=None):
        super(DumpConsumer, self).__init__(hz, parent)
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
    import sys
    from boing.eventloop.EventLoop import EventLoop
    if len(sys.argv)<2:
        print("usage: %s <seconds>"%sys.argv[0])
        sys.exit(1)
    class DebugConsumer(Consumer):
        def __init__(self, hz=None):
            super().__init__(hz)
            self.store = {}
        def _refresh(self):
            super()._refresh()
            print("%s got:"%self.name)
            for producer, products in self.store.items():
                print("  %s from %s"%(products, producer.name))
            self.store = {}
        def _consume(self, products, producer):
            self.store[producer] = products
    def produce(tid, producer, product):
        producer._postProduct(product)
    # init producers
    prod1 = Producer()
    prod1.name = "prod1"
    EventLoop.repeat_every(0.2, produce, prod1, "statue")
    prod2 = Producer()
    prod2.name = "prod2"
    EventLoop.repeat_every(0.7, produce, prod2, "temple")
    # init consumers
    cons1 = DebugConsumer()
    cons1.subscribeTo(prod1)
    cons1.subscribeTo(prod2)
    cons1.name = "cons1"
    cons2 = DebugConsumer(0.8)
    cons2.subscribeTo(prod1)
    cons2.subscribeTo(prod2)
    cons2.name = "cons2"
    # run
    EventLoop.runFor(int(sys.argv[1]))
