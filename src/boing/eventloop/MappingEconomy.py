# -*- coding: utf-8 -*-
#
# boing/eventloop/MappingEconomy.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections

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
        OnDemandProducer._postProduct(self, product)

    @staticmethod
    def filter(product, requests):
        """Return the subset of 'product' that matches 'requests'."""
        subset = None
        if isinstance(requests, collections.Set):
            if isinstance(product, ExtensibleTree):
                for key in requests:
                    matches = product.filter(key, reuse=True)
                    if matches is not None:
                        if subset is None: subset = matches
                        else: subset.update(matches, reuse=True)
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
    def match(path, requests):
        """Return True if 'path' matches 'requests'."""
        rvalue = False
        if isinstance(requests, collections.Set):
            for item in requests:
                if matching.matchPaths(path, item):
                    rvalue = True ; break
        elif requests is OnDemandProducer.ANY_PRODUCT: 
            rvalue = True
        else:
            rvalue = matching.matchPaths(path, request)
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
