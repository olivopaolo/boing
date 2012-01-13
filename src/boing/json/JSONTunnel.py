# -*- coding: utf-8 -*-
#
# boing/json/JSONTunnel.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import json

from PyQt4 import QtCore 

import boing.json
from boing.eventloop.MappingEconomy import MappingProducer, parseRequests
from boing.eventloop.OnDemandProduction import OnDemandProducer, SelectiveConsumer
from boing.eventloop.ProducerConsumer import Consumer
from boing.slip.SlipDataIO import SlipDataReader, SlipDataWriter
from boing.tcp.TcpSocket import TcpConnection
from boing.tcp.TcpServer import TcpServer
from boing.udp.UdpSocket import UdpListener, UdpSender
from boing.url import URL
from boing.utils.DataIO import DataReader, DataWriter
from boing.utils.ExtensibleTree import ExtensibleTree

class JSONEncoder(MappingProducer, SelectiveConsumer):
    """Encode received products using JSON protocol."""
    def __init__(self, requests=OnDemandProducer.ANY_PRODUCT, parent=None):
        MappingProducer.__init__(self, {"str", "data"}, parent=parent)
        SelectiveConsumer.__init__(self, requests)
        self._postdata = False
        self._poststr = False

    def __del__(self):
        MappingProducer.__del__(self)        
        SelectiveConsumer.__del__(self)

    def _checkRef(self):
        MappingProducer._checkRef(self)
        SelectiveConsumer._checkRef(self)
    
    def _updateOverallDemand(self):
        MappingProducer._updateOverallDemand(self)
        self._postdata = MappingProducer.matchDemand("data", self._overalldemand)
        self._poststr = MappingProducer.matchDemand("str", self._overalldemand)

    def _consume(self, products, producer):
        for p in products:
            try:
                jsoncode = json.dumps(p, cls=boing.json.ProductEncoder, 
                                      separators=(',',':'))
            except TypeError:
                pass
            else:
                if self._overalldemand:
                    product = ExtensibleTree()
                    if self._postdata: product.data = jsoncode.encode() 
                    if self._poststr: product.str = jsoncode
                    self._postProduct(product)


class JSONDecoder(MappingProducer, SelectiveConsumer):
    """Decode received JSON string to products."""
    def __init__(self, productoffer=None, requests={"str", "data"}, parent=None):
        MappingProducer.__init__(self, productoffer, parent=parent)
        SelectiveConsumer.__init__(self, requests)

    def __del__(self):
        MappingProducer.__del__(self)        
        SelectiveConsumer.__del__(self)

    def _checkRef(self):
        MappingProducer._checkRef(self)
        SelectiveConsumer._checkRef(self)

    def subscribeTo(self, observable, **kwargs):
        """kwarg 'requests' is also accepted."""
        rvalue = False
        for key in kwargs.keys():
            if key!="requests":
                raise TypeError(
                    "subscribeTo() got an unexpected keyword argument '%s'"%key)
        if isinstance(observable, OnDemandProducer):
            if "requests" in kwargs:
                rvalue = observable.addObserver(self, requests=kwargs["requests"])
            elif "str" in self._requests:
                offer = observable.productOffer()
                if offer=="str" \
                        or isinstance(offer, collections.Container) \
                        and "str" in offer:
                    rvalue = observable.addObserver(self, requests="str")
                else:
                    rvalue = observable.addObserver(self, requests=self._requests)
            else:
                rvalue = observable.addObserver(self, requests=self._requests)
        else:
            rvalue = Consumer.subscribeTo(self, observable) 
        return rvalue

    def _consume(self, products, producer):
        for p in products:
            jsoncode = None
            if "str" in p: jsoncode = p["str"]
            elif "data" in p: jsoncode = p["data"].decode()
            if jsoncode:
                decoded = json.loads(jsoncode, object_hook=boing.json.productHook)
                self._postProduct(decoded)

# ---------------------------------------------------------------------

def JSONReader(url):
    if not isinstance(url, URL): url = URL(str(url))
    decoder = JSONDecoder()
    if url.scheme in ("json", "json.udp"):
        endpoint = DataReader(UdpListener(url), parent=decoder)
        decoder.subscribeTo(endpoint)
    elif url.scheme=="json.tcp":
        class ClientWaiter(QtCore.QObject):
            def __init__(self, parent):
                QtCore.QObject.__init__(self, parent)
                self.socket = None
            def newConnection(self): 
                server = self.sender()
                conn = server.nextPendingConnection()
                if not self.socket:
                    reader = SlipDataReader(conn, parent=decoder)
                    self.parent().subscribeTo(reader)
                    self.socket = conn
                    self.socket.disconnected.connect(self.disconnected)
                else:
                    conn.close()
            def disconnected(self):
                decoder = self.parent()
                for o in decoder.observed():
                    decoder.unsubscribeFrom(o)
                self.socket = None
        waiter = ClientWaiter(parent=decoder)
        server = TcpServer(url.site.host, url.site.port, parent=decoder)
        server.newConnection.connect(waiter.newConnection)
    else:
        decoder = None
        print("Unrecognized JSON url:", url)
    return decoder    


def JSONWriter(url):
    if not isinstance(url, URL): url = URL(str(url))
    req = url.query.data.get('req')
    kwargs = {"requests": parseRequests(req)} if req is not None \
        else dict()
    encoder = JSONEncoder(**kwargs)
    '''    if url.kind in (URL.ABSPATH, URL.RELPATH) \
            or url.scheme=="tuio.file" \
            or (url.scheme=="tuio" and not str(url.site)):
        consumer = LogFile(File(url, File.WriteOnly), parent=encoder)
        consumer.subscribeTo(encoder)'''
    if url.scheme in ("json", "json.udp"):
        endpoint = DataWriter(UdpSender(url), parent=encoder)
        endpoint.subscribeTo(encoder)
    elif url.scheme.endswith("json.tcp"):
        endpoint = SlipDataWriter(TcpConnection(url), parent=encoder)
        endpoint.encoderDevice().setOption("nodelay")
        endpoint.subscribeTo(encoder)
    else:
        encoder = None
        print("Unrecognized JSON url:", url)
    return encoder
