# -*- coding: utf-8 -*-
#
# boing/core/NoncompetitiveProducer.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import weakref

from PyQt4 import QtCore

from boing.core.ProducerConsumer import Producer

# -------------------------------------------------------------------

class NoncompetitiveProducer(Producer):
    """It triggers the registered ReactiveObjects each time it has a new
    product. Products are kept until all the registered ReactiveObjects have
    demanded the pending products."""

    def __init__(self, parent=None):
        Producer.__init__(self, parent)
        """List of the pending products."""
        self._products = []
        """Store the index of the last product sent to each reactiveobject,
        so that the same products are not sent twice and it is possible
        to know when event can be removed (see self.__cleanup()).
        self.__history[ReactiveObject] = int """
        self.__history = {}

    def addObserver(self, observer, mode=QtCore.Qt.QueuedConnection):
        if Producer.addObserver(self, observer, mode):
            self.__history[weakref.ref(observer)] = 0
            return True
        else: return False
        
    def removeObserver(self, observer):
        if Producer.removeObserver(self, observer):
            for ref in self.__history.keys():
                if ref() is observer:
                    del self.__history[ref]
                    self.__cleanup()
                    break
            return True
        else: return False

    def clearObservers(self):
        Producer.clearObservers(self)
        self.__history.clear()
        self._products = []

    def products(self, customer=None):
        """Return the list of the new products. If 'customer' is
        None then the entire list is returned, otherwise only the new
        products are insered.  The argument 'customer' is
        necessary to know when a product has been taken by all the
        registered ReactiveObjects."""
        if len(self._products)==0: return []
        else:
            if customer is None: return tuple(self._products)
            else:
                for ref, value in self.__history.items():
                    if ref() is customer:
                        products = self._products[value:] 
                        self.__history[ref] = len(self._products)
                        self.__cleanup() 
                        break
                else: products = tuple(self._products)
                return products

    def _postProduct(self, product):
        """Add a new product and notify it."""
        if tuple(self.observers()):
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
        Producer._checkRef(self)
        # Keep only alive references
        self.__history = dict((ref,value) for (ref,value) in self.__history.items() \
                                          if ref() is not None)

# -------------------------------------------------------------------

if __name__ == '__main__':
    import itertools
    import signal
    import sys
    from boing.core.ProducerConsumer import Consumer
    if len(sys.argv)<2 or not sys.argv[1].isdecimal():
        print("usage: %s <seconds>"%sys.argv[0])
        sys.exit(1)
    class DebugConsumer(Consumer):
        def __init__(self, hz=None):
            Consumer.__init__(self, hz)
            self.store = {}
        def _refresh(self):
            Consumer._refresh(self)
            print("%s got:"%self.name)
            for producer, products in self.store.items():
                print("  %s from %s"%(products, producer.name))
            self.store = {}
        def _consume(self, products, producer):
            self.store[producer] = products
    def production(producer, product):
        return lambda : producer._postProduct(product)
    # Init app
    app = QtCore.QCoreApplication(sys.argv)
    signal.signal(signal.SIGINT, lambda *args: app.quit())
    QtCore.QTimer.singleShot(int(sys.argv[1])*1000, app.quit)
    # Init producers
    prods = []
    for i, (product, period) in enumerate((("statue", 300), ("temple", 700))):
        p = NoncompetitiveProducer()
        p.name = "prod%d"%(i+1)
        f = production(p, product)
        tid = QtCore.QTimer(p)
        tid.timeout.connect(f)
        tid.start(period)
        prods.append(p)
    # Init consumers
    cons = []
    for i, hz in enumerate((None, 1)):
        c = DebugConsumer(hz)
        c.name = "cons%d"%(i+1)
        cons.append(c)
    # Full subscription
    for p, c in itertools.product(prods, cons): 
        p.addObserver(c)
    del p,c
    # Run
    sys.exit(app.exec_())
