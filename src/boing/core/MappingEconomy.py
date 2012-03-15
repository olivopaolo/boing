# -*- coding: utf-8 -*-
#
# boing/core/MappingEconomy.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import datetime
import collections
import weakref

from PyQt4 import QtCore

from boing.core.OnDemandProduction import OnDemandProducer, SelectiveConsumer
from boing.core.ProducerConsumer import Producer
import boing.utils.QPath as QPath

class MappingProducer(OnDemandProducer):

    class TagRecord(object):
        def __init__(self, template):
            self.template = template
            self.requested = False

    def __init__(self, productoffer=None, cumulate=None, parent=None):
        # FIXME: set productoffer
        OnDemandProducer.__init__(self, productoffer, cumulate, 
                                  MappingProducer.filter, parent)
        """Union of all the subscribed consumers' requests."""
        self.__aggregatedemand = QPath.QPath(None)
        self.requestChanged.connect(self._updateAggregateDemand)
        self.__fseq = 0
        # Tag support
        self.__tags = {}
        self.requestChanged.connect(self._updateTags)
        self.__info__source = str(self)
        self._addTag("__info__", 
                     {"__info__":
                          {"timetag": datetime.datetime.now(),
                           "fseq": self.__fseq,
                           "source": self.__info__source}},
                     update=False)

    def aggregateDemand(self):
        """Return the union of all the subscribed consumers' requests."""
        return self.__aggregatedemand

    def _updateAggregateDemand(self):
        requests = (record.request for record in self._consumers.values())
        self.__aggregatedemand = QPath.join(*requests)

    def _addTag(self, tag, template, update=True):
        """ 'update' should be set to False if this method is used in
        the object constructor."""
        record = MappingProducer.TagRecord(template)
        if update: record.requested = self.isRequested(record.template)
        self.__tags[tag] = record

    def _updateTags(self):
        for record in self.__tags.values():
            record.requested = self.isRequested(record.template)

    def _tag(self, tag):
        """Returns True if 'tag' is requested."""
        record = self.__tags.get(tag)
        return False if record is None else record.requested

    def isRequested(self, product):
        # Faster than the parent class implementation
        return self.__aggregatedemand.test(product)

    def _postProduct(self, product):
        self.__fseq += 1
        if not isinstance(product, collections.Mapping):
            product = {"product":product}
        if self._tag("__info__"):
            product["__info__"] = {"timetag": datetime.datetime.now(),
                                   "fseq": self.__fseq,
                                   "source": self.__info__source}
        OnDemandProducer._postProduct(self, product)

    @staticmethod
    def filter(product, request):
        """Return the subset of 'product' that matches 'request' or
        None."""
        if request==OnDemandProducer.ANY_PRODUCT:
            rvalue = product
        elif request is None:
            rvalue = None
        else:
            rvalue = request.filter(product)
        return rvalue


class MappingConsumer(SelectiveConsumer):
    """A MappingConsumer's request is always a QPath."""
    
    def __init__(self, request=OnDemandProducer.ANY_PRODUCT, hz=None):
        if request is not None and not isinstance(request, QPath.QPath):
            request = QPath.QPath(request)
        SelectiveConsumer.__init__(self, request, hz)

    def setRequest(self, request):
        if request is not None and not isinstance(request, QPath.QPath):
            request = QPath.QPath(request)
        SelectiveConsumer.setRequest(self, request)

# -------------------------------------------------------------------

class HierarchicalProducer(MappingProducer):

    class _PostConsumer(MappingConsumer):
        """It forwards all the products of the parent
        HierarchicalProducer's posts as products of the
        HierarchicalProducer itself."""
        def __init__(self, ref):
            MappingConsumer.__init__(self, request=None)
            self.__ref = ref

        def _consume(self, products, producer):
            for p in products:
                MappingProducer._postProduct(self.__ref(), p)

    def __init__(self, productoffer=None, cumulate=None, parent=None):
        # FIXME: set productoffer
        MappingProducer.__init__(self, productoffer, cumulate, parent)
        """If serial, the products of the post Nodes are the only
        output of this producer."""
        self.__serial = False
        """List of the registered post nodes."""
        self._post = []
        """Forwards the produced products to the post Nodes before the
        standard forwarding."""
        self._postProducer = MappingProducer(productoffer)
        self._postProducer.requestChanged.connect(self.requestChanged)
        """Receives the products from the post Nodes and it forwards them
        as standard products."""
        self._postConsumer = HierarchicalProducer._PostConsumer(weakref.ref(self))

    def isPostSerial(self):
        return self.__serial

    def setPostSerial(self, serial):
        if self.__serial!=serial:
            self.__serial = serial
            # If there are no posts, serial is not influent
            if self._post: self.requestChanged.emit()

    def addPost(self, node, mode=QtCore.Qt.QueuedConnection, serial=None):
        self._post.append(node)
        self._postProducer.addObserver(node, mode=mode)
        self._postConsumer.subscribeTo(node, mode=mode)        
        if serial is not None and self.__serial!=serial: 
            self.setPostSerial(serial)
        return self

    def _updateAggregateDemand(self):
        MappingProducer._updateAggregateDemand(self)
        # The standard aggregate demand is set as the request of the
        # postConsumer
        self._postConsumer.setRequest(self.aggregateDemand())

    def isRequested(self, product):
        """A product is requested if it is demanded from:
         - one of the posts 
         - one of the subscribed consumers, if it is not serial or 
           if it is serial, but there are no post."""
        return \
            self._post and self._postProducer.aggregateDemand().test(product) \
            or not self.__serial or not self._post \
            and MappingProducer.isRequested(self, product)

    def _postProduct(self, product):
        # Forward the product to the posts
        self._postProducer._postProduct(product)
        # Standard production
        if not self.__serial or not self._post:
            MappingProducer._postProduct(self, product)


class HierarchicalConsumer(MappingConsumer):

    class _PreConsumer(MappingConsumer):
        """It forwards all the products of the parent
        HierarchicalConsumer's pre as products of the
        HierarchicalConsumer itself."""
        def __init__(self, ref, request):
            MappingConsumer.__init__(self, request=request)
            self.__ref = ref

        def _consume(self, products, producer):
            self.__ref()._consume(products, producer)

    def __init__(self, request=OnDemandProducer.ANY_PRODUCT, hz=None):
        MappingConsumer.__init__(self, request, hz)
        """If serial, the products from the pre Nodes are the only 
        input of the standard consumption."""
        self.__serial = False
        """List of the registered pre nodes."""
        self._pre = []
        """Forwards the received products to the pre Nodes before the
        standard consumption."""
        self._preProducer = MappingProducer()
        self._preProducer.requestChanged.connect(self._updateRequest)
        """Receives the products from the pre Nodes and it passes them
        to the standard consumption."""
        # The standard request is set as the one of the preConsumer
        self._preConsumer = HierarchicalConsumer._PreConsumer(weakref.ref(self), 
                                                             request)

    def isPreSerial(self):
        return self.__serial

    def setPreSerial(self, serial):
        if self.__serial!=serial:
            self.__serial = serial
            if self._pre: self._updateRequest()

    def addPre(self, node, mode=QtCore.Qt.QueuedConnection, serial=None):
        self._pre.append(node)
        self._preProducer.addObserver(node, mode=mode)
        self._preConsumer.subscribeTo(node, mode=mode)
        if serial is not None: self.setPreSerial(serial)
        return self

    def _updateRequest(self):
        if not self.__serial or not self._pre:
            # pre & self
            join = QPath.join(self._preConsumer.request(), 
                              self._preProducer.aggregateDemand())
            MappingConsumer.setRequest(self, join)
        else:
            # pre only
            MappingConsumer.setRequest(self, self._preProducer.aggregateDemand())

    def setRequest(self, request):
        # The standard request is set as the one of the preConsumer
        self._preConsumer.setRequest(request)
        if not self.__serial or not self._pre: self._updateRequest()

    def _refresh(self):
        for observable in self.queue():
            if isinstance(observable, Producer):
                products = observable.products(self)
                # Forward the products to the pre
                for product in products:
                    self._preProducer._postProduct(product)
                if not self.__serial or not self._pre:
                    # Standard consumption
                    self._consume(products, observable)

# -------------------------------------------------------------------

class Node(HierarchicalProducer, HierarchicalConsumer):
    def __init__(self, productoffer=None, cumulate=None, 
                 request=OnDemandProducer.ANY_PRODUCT, hz=None,
                 parent=None):
        HierarchicalProducer.__init__(self, productoffer, cumulate, parent)
        HierarchicalConsumer.__init__(self, request, hz)

    def __del__(self):
        HierarchicalProducer.__del__(self)
        HierarchicalConsumer.__del__(self)

    def _checkRef(self):
        HierarchicalProducer._checkRef(self)
        HierarchicalConsumer._checkRef(self)
