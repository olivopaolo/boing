# -*- coding: utf-8 -*-
#
# boing/eventloop/MappingEconomy.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import itertools

from boing.eventloop.OnDemandProduction import OnDemandProducer
from boing.utils import matching
from boing.utils.ExtensibleTree import ExtensibleTree

class MappingProducer(OnDemandProducer):
    """A MappingProducer always produces collections.Mapping objects,
    so that products can be mapped using keys. Production requests is
    also handled using keys."""
    def __init__(self, productoffer=None, cumulate=None, parent=None):
        OnDemandProducer.__init__(self, productoffer, cumulate, 
                                  MappingProducer.filter, parent)
        self._overalldemand = set()
        self._functions = list()

    def addObserver(self, *args, **kwargs):
        rvalue = OnDemandProducer.addObserver(self, *args, **kwargs)
        if rvalue: self._updateOverallDemand()
        return rvalue

    def removeObserver(self, *args, **kwargs):
        rvalue = OnDemandProducer.removeObserver(self, *args, **kwargs)
        if rvalue: self._updateOverallDemand()
        return rvalue

    def clearObservers(self):
        OnDemandProducer.clearObservers(self)
        self._overalldemand = set()        

    def overallDemand(self):
        return self._overalldemand
    
    def addFunction(self, target, callback, dependences, *args, **kwargs):
        """Add a function that will be invoked any time a product is
        posted if all dendences (i.e. a list of paths) are satisfied,
        which means if the product contains all the paths in
        dependences. 'target' can be a function that returns a path or
        even a path and it will be used to store the result of the
        function into the current product. To 'callback' and 'target',
        if it is a function, it will be passed as argument the list of
        dependences concretized (no more regexp) and associated to the
        value found in the current product, i.e. ((k,v),(k,v),...) """
        self._functions.append((target, callback, dependences, args, kwargs))

    def _updateOverallDemand(self):
        self._overalldemand = set()
        for record in self._consumers.values():
            if record.requests is OnDemandProducer.ANY_PRODUCT:
                self._overalldemand = OnDemandProducer.ANY_PRODUCT
                break
            elif isinstance(record.requests, collections.Set): 
                self._overalldemand.update(record.requests)
            elif record.requests is not None:
                self._overalldemand.add(record.requests)

    def _postProduct(self, product):
        if not isinstance(product, collections.Mapping):
            raise TypeError("product must be collections.Mapping, not %s"%
                            product.__class__.__name__)
        fresult = self._applyFunctions(product)
        if fresult: product.update(fresult, reuse=True)
        OnDemandProducer._postProduct(self, product)

    def _applyFunctions(self, product, repository=None):
        """Apply all the registered functions to the current
        product. 'repository' is used as an alternative is the
        function's dependences cannot be found inside the product, but
        at least one dependence must be found in the product. (See
        StateMachine)"""
        rvalue = None
        # 'cases' is the list of dependences concretized using product
        # and repository. Each dependences can have more than one
        # concretizations.
        cases = list()
        for target, callback, dependences, args, kwargs in self._functions:
            del cases[:]
            for path in dependences:
                subtree = product.filter(path, reuse=True)
                if subtree is not None:
                    cases.append(subtree.flatten().items())
                elif repository is not None:
                    cases.append(None)
                else: del cases[:] ; break
            if any(cases):
                for i, case in enumerate(cases):
                    if not case:
                        subtree = repository.filter(dependences[i], 
                                                    reuse=True)
                        if subtree is not None:
                            cases[i] = subtree.flatten().items()
                        else: break
                else:
                    # If all dependences have been solved
                    for case in itertools.product(*cases):
                        targetcase = target(case) \
                            if isinstance(target, collections.Callable) \
                            else target
                        for record in self._consumers.values():
                            if MappingProducer.matchDemand(targetcase, 
                                                           record.requests):
                                if rvalue is None: rvalue = ExtensibleTree()
                                rvalue.set(targetcase, 
                                           callback(case, *args, **kwargs))
                                break
        return rvalue

    @staticmethod
    def filter(product, requests):
        """Return the subset of 'product' that matches 'requests'."""
        subset = None
        if isinstance(requests, collections.Set):
            if isinstance(product, ExtensibleTree):
                for key in requests:
                    subtree = product.filter(key, reuse=True)
                    if subtree is not None:
                        if subset is None: subset = subtree
                        else: subset.update(subtree, reuse=True)
            elif isinstance(product, collections.MutableMapping):
                for key in requests:
                    if subset is None: 
                        subset = type(product)(matching.filterItems(product, key))
                    else:
                        subset.update(
                            type(product)(matching.filterItems(product, key)))
                if not subset: subset = None
            elif isinstance(product, collections.Mapping):
                raise NotImplementedError("collections.Mapping case")
        elif requests is OnDemandProducer.ANY_PRODUCT:
            subset = product
        elif isinstance(product, ExtensibleTree):
            subset = product.filter(requests, reuse=True)
        elif isinstance(product, collections.MutableMapping):
            subset = type(product)(matching.filterItems(product, requests))
            if not subset: subset = None
        elif isinstance(product, collections.Mapping):
            raise NotImplementedError("Unmutable mapping case.")    
        return subset

    @staticmethod
    def matchDemand(path, demand):
        """Return True if 'path' matches the current product demand."""
        rvalue = False
        if isinstance(demand, collections.Set):
            for item in demand:
                if matching.matchPaths(path, item):
                    rvalue = True ; break
        elif demand is OnDemandProducer.ANY_PRODUCT: 
            rvalue = True
        else:
            rvalue = matching.matchPaths(path, demand)
        return rvalue

'''
class MappingConsumer(SelectiveConsumer):

    def __init__(self, requests=OnDemandProducer.ANY_PRODUCT, hz=None):
        """'requests' must be set, None or OnDemandProducer.ANY_PRODUCT."""
        if requests not in (None, OnDemandProducer.ANY_PRODUCT) \
                and not isinstance(requests, set): 
            raise ValueError(
                "requests must be set, None or OnDemandProducer.ANY_PRODUCT, not %s"%
                restrictions.__class__.__name__)
        SelectiveConsumer.__init__(self, requests, hz)'''
                
# -------------------------------------------------------------------

def parseRequests(requests):
    try:
        req = set()
        path = []
        while requests:
            part, comma, requests = requests.partition(",")
            index = part.find("(")
            if index==-1:
                index = part.find(")")
                if index==-1:
                    if path: path.append(part.strip())
                    else: req.add(part.strip())
                elif index==len(part)-1:
                    if path: 
                        path.append(part[:-1].strip())
                        req.add(tuple(path))
                        path = []
                    else: raise Exception()
                else: raise Exception()
            elif index==0: 
                index = part.find(")")
                if index==-1:
                    if path: raise Exception()
                    else: path.append(part[1:].strip())
                elif index==len(part)-1:
                    if path: raise Exception()
                    else: req.add(part[1:-1].strip())
                else: raise Exception()            
            else: raise Exception()
        if path: raise Exception()
    except Exception: 
        print("Wrong format: %s"%requests)
    else: 
        return req
