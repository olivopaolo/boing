# -*- coding: utf-8 -*-
#
# boing/core/querypath.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from boing.core import economy
from boing.utils import QPath, assertIsInstance

class QRequest(economy.Request):
    """The QRequest is a consumer request defined by a QPath."""

    def __init__(self, string):
        self._query = QPath.QPath(string)

    def query(self):
        return self._query

    def test(self, product):
        return isinstance(product, economy.UndefinedProduct) \
            or self._query.test(product)

    def items(self, product):
        return self._query.items(product)

    def filter(self, product):
        return self._query.filter(product)

    def filterout(self, product):
        return self._query.filterout(product)

    def __eq__(self, other):
        return isinstance(other, QRequest) \
            and other not in (economy.Request.ANY, economy.Request.NONE) \
            and self._query==other.query()
        
    def __add__(self, other):
        if other is economy.Request.ANY or self==other:
            rvalue = other
        elif other is economy.Request.NONE:
            rvalue = self
        elif isinstance(other, QRequest):
            rvalue = QRequest(QPath.join(self._query, other.query()))
        elif isinstance(other, economy.Request):
            rvalue = economy._CompositeRequest(self, other)
        else: raise TypeError(
            "Expected type Request, not '%s'"%type(other).__name__)
        return rvalue

    def __hash__(self):
        return hash(self._query)

    def __repr__(self):
        return "Request('%s')"%self._query



