# -*- coding: utf-8 -*-
#
# boing/core/__init__.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

"""The module :mod:`boing.core` contains the classes that constitute
the infrastructure of |boing| pipelines.

"""

import collections as _collections
import copy as _copy
import itertools as _itertools

# Facade pattern to make things easier.
from boing.core.economy import \
    Offer, Request, _CompositeRequest, LambdaRequest, \
    Producer, Consumer, Worker, BaseWorker, NopWorker, WiseWorker, Functor, \
    Composite, CompositeProducer, CompositeConsumer, CompositeWorker

from boing.utils import querypath as _querypath
from  boing.utils import quickdict as _quickdict

class QRequest(Request):
    """The QRequest is a Request defined by a QPath.

    """
    def __init__(self, string):
        self._query = _querypath.QPath(string)

    def query(self):
        """Return the :cls:`boing.utils.querypath.QPath` instance used
        to filter items."""
        return self._query

    def test(self, product):
        """Return whether *product* matches the request."""
        return self.query().test(product, wildcard=Offer.UNDEFINED)

    def items(self, product):
        """Return an iterator over the *product*'s items ((key, value)
        pairs) that match the request, if *product* can be subdivided, otherwise
        return the pair (None, *product)."""
        return self.query().items(product)

    def __eq__(self, other):
        return isinstance(other, QRequest) and self.query()==other.query()

    def __add__(self, other):
        return NotImplemented if not isinstance(other, Request) \
            else other if other is Request.ANY or self==other \
            else self if other is Request.NONE \
            else QRequest(self.query()+other.query()) if isinstance(other, QRequest) \
            else _CompositeRequest(self, other)

    def __hash__(self):
        return hash(self.query())

    def __repr__(self):
        return "QRequest('%s')"%self.query()

def _merge(previous, items, tocopy):
    rvalue = previous
    for path, value in items if items is not None else tuple():
        rvalue = _querypath.set_(rvalue, path, value, tocopy)
    return rvalue

class _ConcreteMerge(economy.Functor.MergeBlender):
    def blend(self, products, results):
        for product, items in _itertools.zip_longest(products, results):
            yield _merge(product, items, False)

class _ConcreteMergeCopy(economy.Functor.MergeBlender):
    def __repr__(self): return "Blender.MERGECOPY"

    def blend(self, products, results):
        for product, items in _itertools.zip_longest(products, results):
            yield  product if not items \
                else _merge(product, items, True)

class _ConcreteResultOnly(economy.Functor.ResultOnlyBlender):
    def blend(self, products, results):
        for product, items in _itertools.zip_longest(products, results):
            yield _merge(_quickdict(), items, False)

economy.Functor.MERGE = _ConcreteMerge()
economy.Functor.MERGECOPY = _ConcreteMergeCopy()
economy.Functor.RESULTONLY = _ConcreteResultOnly()

# -------------------------------------------------------------------
