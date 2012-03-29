# -*- coding: utf-8 -*-
#
# boing/core/ProducerConsumer.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from boing.core.ReactiveObject import Observable, DelayedReactive

class Producer(Observable):

    def products(self, customer=None):
        """Return the produced products. The argument 'customer' must
        be used to define who is demanding the products."""
        raise NotImplementedError()

    def _postProduct(self, product):
        """Notify a new product."""
        raise NotImplementedError()


class Consumer(DelayedReactive):
    """Anytime it is triggered, it requires all the available products
    to all producers it is subscribed to."""
    def __init__(self, hz=None):
        DelayedReactive.__init__(self, hz)

    def _refresh(self):
        for observable in self.queue():
            if isinstance(observable, Producer):
                products = observable.products(self)
                self._consume(products, observable)

    def _consume(self, products, producer):
        """The consumer normally must not modify the received
        products, because they could be shared with other consumers."""        
        pass
