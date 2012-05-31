# -*- coding: utf-8 -*-
#
# boing/core/__init__.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import copy
import itertools

from boing.core import economy
from boing.core import querypath
from boing.utils import quickdict

# Facade pattern to make things easier.

Product = quickdict

Offer = economy.Offer

Request = querypath.QRequest

Producer = economy.Producer

Consumer = economy.Consumer

Functor = economy.Functor


def _merge(previous, items):
    rvalue = previous
    if items:
        for path, value in items:
            split = path.split(".")
            if len(split)==1: rvalue[path] = value
            else:
                node = rvalue
                for key in split[:-1]:
                    if isinstance(node, collections.Sequence):
                        key = int(key)
                    node = node[key]
                key = split[-1] 
                if isinstance(node, collections.Sequence):
                    key = int(key)
                node[key] = value
    return rvalue

class ConcreteMerge(Functor.MergeBlender):

    @staticmethod    
    def blend(products, results):
        for product, items in itertools.zip_longest(products, results):
            yield _merge(product, items)


class ConcreteMergeCopy(Functor.MergeBlender):    

    @staticmethod    
    def blend(products, results):
        for product, items in itertools.zip_longest(products, results):
            yield  product if not items \
                else _merge(copy.deepcopy(product), items)


class ConcreteResultOnly(Functor.ResultOnlyBlender):    

    @staticmethod    
    def blend(products, results):
        for items in filter(None, results):
            yield _merge(Product(), items)


Functor.MERGE = ConcreteMerge
Functor.MERGECOPY = ConcreteMergeCopy
Functor.RESULTONLY = ConcreteResultOnly

