# -*- coding: utf-8 -*-
#
# boing/core/querypath.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from boing.core.economy import Offer, Request, _CompositeRequest
from boing.utils import QPath, assertIsInstance

class QRequest(Request):
    """The QRequest is a Request defined by a QPath."""
    def __init__(self, string):
        self._query = QPath.QPath(string)

    def query(self):
        """Return the querypath string."""
        return self._query

    def test(self, product):
        """Return whether *product* matches the request."""
        return isinstance(product, Offer.UndefinedProduct) \
            or self._query.test(product)

    def items(self, product):
        """Return an iterator over the *product*'s items ((key, value)
        pairs) that match the request, if *product* can be subdivided, otherwise
        return the pair (None, *product)."""
        return self._query.items(product)

    def filter(self, product):
        """Return the subset of *product* that matches the request, if
        *product* can be subdivided, otherwise return *product*, if
        product matches the request, else return None."""
        return self._query.filter(product)

    def filterout(self, product):
        """Return the subset of *product* that does not match the
        request, if *product* can be subdivided, otherwise return
        *product*, if product does not match the request, else return
        None."""
        return self._query.filterout(product)

    def __eq__(self, other):
        return isinstance(other, QRequest) \
            and self._query==other.query()
        
    def __add__(self, other):
        if other is Request.ANY or self==other:
            rvalue = other
        elif other is Request.NONE:
            rvalue = self
        elif isinstance(other, QRequest):
            rvalue = QRequest(QPath.join(self._query, other.query()))
        elif isinstance(other, Request):
            rvalue = _CompositeRequest(self, other)
        else: raise TypeError(
            "Expected type Request, not '%s'"%type(other).__name__)
        return rvalue

    def __hash__(self):
        return hash(self._query)

    def __repr__(self):
        return "QRequest('%s')"%self._query



