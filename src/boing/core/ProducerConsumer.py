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
        """Return the produced products. 'customer' should be used to
        define who is demanding the products."""
        raise NotImplementedError()

    def _postProduct(self, product):
        raise NotImplementedError()


class Consumer(DelayedReactive):
    """Anytime it is triggered, it requires the available products to
    all producers it is subscribed to."""

    def _refresh(self):
        for observable in self.queue():
            if isinstance(observable, Producer):
                self._consume(observable.products(self), observable)

    def _consume(self, products, producer):
        """It can be overridden to define business logic, but do not invoke it
        directly."""
        pass
