# -*- coding: utf-8 -*-
#
# boing/core/__init__.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.


from boing.core import economy
from boing.utils import quickdict

class Product(quickdict):
    def __repr__(self):
        return "Product(%s)"%",".join("%s=%s"%(k,repr(v)) for k,v in self.items())

class _ConcreteUndefined(Product, economy.UndefinedProduct):
    """Concrete undefined product."""
    def __init__(self): super().__init__()
    def __repr__(self): return "Product.UNDEFINED"

Product.UNDEFINED = _ConcreteUndefined()

# -------------------------------------------------------------------
# FIXME: Develop QPath.set

import collections as _collections
import copy as _copy
import itertools as _itertools

def _merge(previous, items):
    rvalue = previous
    if items:
        for path, value in items:
            split = path.split(".")
            if len(split)==1: rvalue[path] = value
            else:
                node = rvalue
                for key in split[:-1]:
                    if isinstance(node, _collections.Sequence):
                        key = int(key)
                    node = node[key]
                key = split[-1] 
                if isinstance(node, _collections.Sequence):
                    key = int(key)
                node[key] = value
    return rvalue

class _ConcreteMerge(economy.Functor.MergeBlender):
    def blend(self, products, results):
        for product, items in _itertools.zip_longest(products, results):
            yield _merge(product, items)

class _ConcreteMergeCopy(economy.Functor.MergeBlender):    
    def __repr__(self): return "Blender.MERGECOPY"

    def blend(self, products, results):
        for product, items in _itertools.zip_longest(products, results):
            yield  product if not items \
                else _merge(_copy.deepcopy(product), items)

class _ConcreteResultOnly(economy.Functor.ResultOnlyBlender):    
    def blend(self, products, results):
        for items in filter(None, results):
            yield _merge(Product(), items)


economy.Functor.MERGE = _ConcreteMerge()
economy.Functor.MERGECOPY = _ConcreteMergeCopy()
economy.Functor.RESULTONLY = _ConcreteResultOnly()

# -------------------------------------------------------------------
