#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# boing/test/core/test_economy.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import itertools
import unittest
import weakref

from PyQt4 import QtCore

from boing.core.economy import \
    Offer, Request, Producer, Consumer, \
    FunctorRequest, _CustomerProducer
from boing.core.observer import Observer
from boing.test import QtBasedTest
from boing.test.core.test_observer import testReact


class TestRequest(unittest.TestCase):

    def setUp(self):
        self.request = FunctorRequest(lambda product: bool(product))

    def test_ANY(self):
        self.assertTrue(Request.ANY.test("ANYTHING"))
        self.assertEquals(Request.ANY, Request.ANY)
        self.assertNotEquals(Request.ANY, Request.NONE)
        sum = Request.ANY + self.request
        self.assertEquals(sum, Request.ANY)
        sum += self.request
        self.assertEquals(sum, Request.ANY)
        self.assertRaises(TypeError, Request.ANY.__add__, "ANYTHING")
        hash(Request.ANY)

    def test_NONE(self):
        self.assertFalse(Request.NONE.test("ANYTHING"))
        self.assertEquals(Request.NONE, Request.NONE)
        self.assertNotEquals(Request.NONE, Request.ANY)
        sum = Request.NONE + self.request
        self.assertEquals(sum, self.request)
        self.assertRaises(TypeError, Request.NONE.__add__, "ANYTHING")
        hash(Request.NONE)

class TestFunctorRequest(unittest.TestCase):

    def setUp(self):
        self.functor = lambda product: bool(product)

    def test_creation_empty(self):
        request = FunctorRequest()

    def test_creation_None(self):
        request = FunctorRequest(None)

    def test_creation_raises(self):
        self.assertRaises(TypeError, FunctorRequest, "wrong")

    def test_test(self):
        request = FunctorRequest()
        self.assertRaises(NotImplementedError, request.test, "ANYTHING")
        request = FunctorRequest(self.functor)
        self.assertTrue(request.test(True))
        self.assertFalse(request.test(False))

    def test_equal(self):
        self.assertEqual(FunctorRequest(), FunctorRequest())
        self.assertEqual(FunctorRequest(None), FunctorRequest(None))
        self.assertEqual(FunctorRequest(self.functor), 
                         FunctorRequest(self.functor))

    def test_hash(self):
        hash(FunctorRequest())
        hash(FunctorRequest(None))
        hash(FunctorRequest(self.functor))


class Test_CompositeRequest(unittest.TestCase):

    def setUp(self):
        self.truerequest = FunctorRequest(
            lambda product: bool(product))
        self.tuplerequest = FunctorRequest(
            lambda product: isinstance(product, tuple))

    def test_test(self):
        composite = self.truerequest + self.tuplerequest
        self.assertFalse(self.truerequest.test(tuple()))
        self.assertFalse(self.tuplerequest.test(True))
        self.assertTrue(composite.test(True))
        self.assertTrue(composite.test(tuple()))
        self.assertFalse(composite.test(False))

    def test_add(self):
        composite = self.truerequest + self.tuplerequest
        self.assertEqual(composite, self.truerequest + self.tuplerequest)
        self.assertEqual(composite, composite + self.truerequest + self.tuplerequest)

# -------------------------------------------------------------------

def eqRequestFactory(other): 
    return FunctorRequest(lambda value: value==other)

def storeProducts(consumer, products, producer):
    storage = consumer.__dict__.setdefault("storage", list())
    storage.extend(products)

class TestProducer(QtBasedTest):

    # FIXME: Add tag tests

    def test_creation(self):
        producer = Producer(offer=Offer.UNDEFINED)
        ref = weakref.ref(producer)
        del producer
        self.assertIsNone(ref())

    def test_creation_wrong_arg(self):
        self.assertRaises(TypeError, Producer, wrong="wrong")

    def test_creation_demandChanged(self):
        producer = Producer(offer=Offer.UNDEFINED, 
                            demandChanged=lambda : None)

    def test_connect_demandChanged(self):
        producer = Producer(offer=Offer.UNDEFINED)
        producer.demandChanged.connect(lambda : None)

    def test_creation_demandedOfferChanged(self):
        producer = Producer(offer=Offer.UNDEFINED, 
                            demandedOfferChanged=lambda : None)

    def test_connect_demandedOfferChanged(self):
        producer = Producer(offer=Offer.UNDEFINED)
        producer.demandedOfferChanged.connect(lambda : None)

    def test_offer(self):
        producer = Producer(offer=Offer.UNDEFINED)
        self.assertEqual(producer.offer(), Offer.UNDEFINED)
        offer = Offer("statue", "painting")
        producer = Producer(offer=offer)
        self.assertEqual(producer.offer(), offer)
        self.assertNotEqual(producer.offer(), Offer("obelisk"))
        self.assertNotEqual(producer.offer(), Offer("statue"))

    def test_meetsRequest(self):
        producer = Producer(offer=Offer.UNDEFINED)
        self.assertFalse(producer.meetsRequest(eqRequestFactory("statue")))
        self.assertFalse(producer.meetsRequest(Request.ANY))
        producer = Producer(Offer("statue", "obelisk"))
        self.assertTrue(producer.meetsRequest(eqRequestFactory("statue")))
        self.assertTrue(producer.meetsRequest(Request.ANY))
        self.assertFalse(producer.meetsRequest(eqRequestFactory("painting")))
        self.assertTrue(producer.meetsRequest(
                eqRequestFactory("statue")+eqRequestFactory("obelisk")))

    def test_addObservers(self):
        producer = Producer(offer=Offer.UNDEFINED)
        refprod = weakref.ref(producer)
        self.assertRaises(TypeError, producer.addObserver, None)
        self.assertRaises(TypeError, producer.addObserver, "wrong")
        observer = Observer()
        refobs = weakref.ref(observer)
        self.assertTrue(producer.addObserver(observer))
        self.assertFalse(producer.addObserver(observer))
        consumer = Consumer(Request.NONE)
        refselcons = weakref.ref(consumer)
        self.assertTrue(producer.addObserver(consumer))
        del observer
        self.assertIsNone(refobs())
        del consumer
        self.assertIsNone(refselcons())
        del producer
        self.assertIsNone(refprod())

    def test_aggregateDemand_demandedOffer_isRequested(self):
        producer = Producer(
            offer=Offer("statue", "painting", "obelisk"),
            demandChanged=lambda : setattr(self, "demandTrigger", True),
            demandedOfferChanged=lambda : setattr(self, "offerTrigger", True))
        self.assertEqual(producer.aggregateDemand(), Request.NONE)
        self.assertEqual(producer.demandedOffer(), Offer())
        # Init consumers
        consumers, requests = [], {}
        for item in ("statue", "painting", "obelisk"):
            requests[item] = eqRequestFactory(item)      
        for request in (Request.NONE, #0
                        requests["statue"],   #1
                        requests["statue"],   #2
                        requests["statue"] + requests["obelisk"], #3
                        requests["statue"],   #4
                        Request.ANY,  #5
                        Request.ANY): #6
            consumers.append(Consumer(request))
        del request
        # Add Observer
        self.demandTrigger = False
        self.offerTrigger = False
        producer.addObserver(Observer())
        self.assertEqual(producer.aggregateDemand(), Request.NONE)
        self.assertEqual(producer.demandedOffer(), Offer())
        self.assertFalse(self.demandTrigger)
        self.assertFalse(self.offerTrigger)
        # Incrementally add consumers
        # 0
        producer.addObserver(consumers[0])
        self.assertEqual(producer.aggregateDemand(), Request.NONE)
        self.assertEqual(producer.demandedOffer(), Offer())
        self.assertFalse(self.demandTrigger)
        self.assertFalse(self.offerTrigger)
        # 1
        producer.addObserver(consumers[1])
        self.assertEqual(producer.aggregateDemand(), requests["statue"])
        self.assertEqual(producer.demandedOffer(), Offer("statue"))
        self.assertTrue(self.demandTrigger)
        self.assertTrue(self.offerTrigger)
        self.assertTrue(producer.isRequested("statue"))
        self.assertFalse(producer.isRequested("painting"))
        # 2
        self.demandTrigger = False
        self.offerTrigger = False
        producer.addObserver(consumers[2])
        self.assertEqual(producer.aggregateDemand(), requests["statue"])
        self.assertEqual(producer.demandedOffer(), Offer("statue"))
        self.assertFalse(self.demandTrigger)
        self.assertFalse(self.offerTrigger)
        # 3
        producer.addObserver(consumers[3])
        self.assertEqual(producer.aggregateDemand(), 
                         requests["statue"] + requests["obelisk"])
        self.assertEqual(producer.demandedOffer(), Offer("statue", "obelisk"))
        self.assertTrue(self.demandTrigger)
        self.assertTrue(self.offerTrigger)
        self.assertTrue(producer.isRequested("statue"))
        self.assertTrue(producer.isRequested("obelisk"))
        self.assertFalse(producer.isRequested("painting"))
        # 4
        self.demandTrigger = False
        self.offerTrigger = False
        producer.addObserver(consumers[4])
        self.assertEqual(producer.aggregateDemand(), 
                         requests["statue"] + requests["obelisk"])
        self.assertEqual(producer.demandedOffer(), Offer("statue", "obelisk"))
        self.assertFalse(self.demandTrigger)
        self.assertFalse(self.offerTrigger)
        # 5
        producer.addObserver(consumers[5])
        self.assertEqual(producer.aggregateDemand(), Request.ANY)
        self.assertEqual(producer.demandedOffer(), 
                         Offer("statue", "painting", "obelisk"))
        self.assertTrue(self.demandTrigger)
        self.assertTrue(self.offerTrigger)
        self.assertTrue(producer.isRequested("statue"))
        self.assertTrue(producer.isRequested("obelisk"))
        self.assertTrue(producer.isRequested("painting"))
        # 6
        self.demandTrigger = False
        self.offerTrigger = False
        producer.addObserver(consumers[6])
        self.assertEqual(producer.aggregateDemand(), Request.ANY)
        self.assertEqual(producer.demandedOffer(), 
                         Offer("statue", "painting", "obelisk"))
        self.assertFalse(self.demandTrigger)
        self.assertFalse(self.offerTrigger)
        # Incrementally remove consumers
        # 6
        producer.removeObserver(consumers[6])
        self.assertEqual(producer.aggregateDemand(), Request.ANY)
        self.assertEqual(producer.demandedOffer(), 
                         Offer("statue", "painting", "obelisk"))
        self.assertFalse(self.demandTrigger)
        self.assertFalse(self.offerTrigger)
        # 5
        producer.removeObserver(consumers[5])
        self.assertEqual(producer.aggregateDemand(),
                         requests["statue"] + requests["obelisk"])
        self.assertEqual(producer.demandedOffer(), Offer("statue", "obelisk"))
        self.assertTrue(self.demandTrigger)
        self.assertTrue(self.offerTrigger)
        self.assertTrue(producer.isRequested("statue"))
        self.assertTrue(producer.isRequested("obelisk"))
        self.assertFalse(producer.isRequested("painting"))
        # 4
        self.demandTrigger = False
        self.offerTrigger = False
        producer.removeObserver(consumers[4])
        self.assertEqual(producer.aggregateDemand(), 
                         requests["statue"] + requests["obelisk"])
        self.assertEqual(producer.demandedOffer(), 
                         Offer("statue", "obelisk"))
        self.assertFalse(self.demandTrigger)
        self.assertFalse(self.offerTrigger)
        # 3
        producer.removeObserver(consumers[3])
        self.assertEqual(producer.aggregateDemand(), requests["statue"])
        self.assertEqual(producer.demandedOffer(), Offer("statue"))
        self.assertTrue(self.demandTrigger)
        self.assertTrue(self.offerTrigger)
        self.assertTrue(producer.isRequested("statue"))
        self.assertFalse(producer.isRequested("obelisk"))
        self.assertFalse(producer.isRequested("painting"))
        # 2
        self.demandTrigger = False
        self.offerTrigger = False
        producer.removeObserver(consumers[2])
        self.assertEqual(producer.aggregateDemand(), requests["statue"])
        self.assertEqual(producer.demandedOffer(), Offer("statue"))
        self.assertFalse(self.demandTrigger)
        self.assertFalse(self.offerTrigger)
        # 1
        producer.removeObserver(consumers[1])
        self.assertEqual(producer.aggregateDemand(), Request.NONE)
        self.assertEqual(producer.demandedOffer(), Offer())
        self.assertTrue(self.demandTrigger)
        self.assertTrue(self.offerTrigger)
        # 0
        self.demandTrigger = False
        self.offerTrigger = False
        producer.removeObserver(consumers[0])
        self.assertEqual(producer.aggregateDemand(), Request.NONE)
        self.assertEqual(producer.demandedOffer(), Offer())
        self.assertFalse(self.demandTrigger)
        self.assertFalse(self.offerTrigger)
        # Add all consumers and the clear
        for cons in consumers:
            producer.addObserver(cons)
        self.assertEqual(producer.aggregateDemand(), Request.ANY)
        self.assertEqual(producer.demandedOffer(), 
                         Offer("statue", "painting", "obelisk"))
        self.demandTrigger = False
        self.offerTrigger = False
        producer.clear()
        self.assertEqual(producer.aggregateDemand(), Request.NONE)
        self.assertEqual(producer.demandedOffer(), Offer())
        self.assertTrue(self.demandTrigger)
        self.assertTrue(self.offerTrigger)
        # Add all consumers and delete them during eventloop
        self.assertEqual(len(list(producer.observers())), 0)
        for cons in consumers:
            producer.addObserver(cons)
        del cons
        self.assertEqual(producer.aggregateDemand(), Request.ANY)
        self.assertEqual(producer.demandedOffer(), 
                         Offer("statue", "painting", "obelisk"))
        self.demandTriggerCount = 0
        self.offerTriggerCount = 0
        self.demandTrigger = False
        self.offerTrigger = False
        producer.demandChanged.connect(
            lambda : setattr(self, "demandTriggerCount", self.demandTriggerCount+1))
        producer.demandedOfferChanged.connect(
            lambda : setattr(self, "offerTriggerCount", self.offerTriggerCount+1))
        setter = lambda obj, key, value: obj.__setitem__(key, value)
        QtCore.QTimer.singleShot(300, lambda : setter(consumers, 6, None))
        QtCore.QTimer.singleShot(350, lambda : setter(consumers, 5, None))
        QtCore.QTimer.singleShot(400, lambda : setter(consumers, 4, None))
        QtCore.QTimer.singleShot(450, lambda : setter(consumers, 3, None))
        QtCore.QTimer.singleShot(500, lambda : producer.clear())
        QtCore.QTimer.singleShot(700, self.app.quit)
        # Exec
        self.app.exec_()
        self.assertEqual(producer.aggregateDemand(), Request.NONE)
        self.assertEqual(producer.demandedOffer(), Offer())
        self.assertTrue(self.demandTrigger)
        self.assertTrue(self.offerTrigger)
        self.assertEqual(self.demandTriggerCount, 3)
        self.assertEqual(self.offerTriggerCount, 3)
        
    def production_test(self, mode):
        # Init producers
        producers = []
        def makeFunctor(producer, product, n):
            proxy = weakref.proxy(producer)
            return lambda : self.assertEqual(proxy.postProduct(product), n)
        # Consumers are defined by the product they produce and the number of 
        # Consumers that will be interested to their products.
        for i, (template, n) in enumerate((("statue", 4), 
                                           ("painting", 3),
                                           ("obelisk", 3))):
            producers.append(Producer(offer=Offer.UNDEFINED))
            tid = QtCore.QTimer(producers[i], 
                                timeout=makeFunctor(producers[i], template, n))
            tid.start(20)
        reffirstproducer = weakref.ref(producers[0])
        # Init Observers
        observer = Observer(react=testReact)
        # Consumers are set to that:
        #
        # - the first is deleted during eventloop;
        #
        # - the second won't get anything (request=None)
        #
        # - the third will get everything
        #
        # - the fourth will get only statues
        #
        # - the fifth will get at the beginning only paintings, but
        #   after 400ms it changes for paintings and temples.
        #
        # - the sixth will get both statues and obelisks (sum of requests)
        consumers = []
        for request in (Request.NONE,
                        Request.NONE, Request.ANY,
                        eqRequestFactory("statue"), 
                        eqRequestFactory("painting"),
                        eqRequestFactory("statue") + eqRequestFactory("obelisk")):
            consumers.append(Consumer(request, consume=storeProducts))
        reffirstconsumer = weakref.ref(consumers[0])
        # Forth consumer changes its request during eventloop
        QtCore.QTimer.singleShot(
            400, lambda : consumers[4].setRequest(
                eqRequestFactory("painting") + eqRequestFactory("temple")))
        # Subscriptions
        for producer in producers:
            producer.addObserver(observer, mode)
            for consumer in consumers:
                producer.addObserver(consumer, mode)
        del producer, consumer
        # Delete instances during eventloop
        setter = lambda obj, key, value: obj.__setitem__(key, value)
        QtCore.QTimer.singleShot(
            400, lambda : setter(producers, 0, None))
        QtCore.QTimer.singleShot(
            500, lambda : setter(consumers, 0, None))
        QtCore.QTimer.singleShot(
            600, self.app.quit)
        # Exec
        self.app.exec_()
        # Check element deletion
        self.assertIsNone(reffirstproducer())
        self.assertIsNone(reffirstconsumer())
        for prod in filter(None, producers):
            self.assertEqual(set(prod.observers()), 
                             set(itertools.chain(consumers[1:],
                                                (observer, ))))
        for cons in filter(None, consumers):
            self.assertEqual(set(cons.observed()), set(producers[1:]))
        # Check react func
        self.assertGreater(observer.hit, 0)
        self.assertFalse(hasattr(consumers[1], "storage"))
        self.assertIn("statue", consumers[2].storage)
        self.assertIn("painting", consumers[2].storage)
        self.assertIn("obelisk", consumers[2].storage)
        self.assertIn("statue", consumers[3].storage)
        self.assertNotIn("painting", consumers[3].storage)
        self.assertNotIn("obelisk", consumers[3].storage)
        self.assertIn("painting", consumers[4].storage)
        self.assertIn("statue", consumers[5].storage)
        self.assertNotIn("painting", consumers[5].storage)
        self.assertIn("obelisk", consumers[5].storage)

    def test_production_direct(self):
        self.production_test(QtCore.Qt.DirectConnection)

    def test_production_queued(self):
        self.production_test(QtCore.Qt.QueuedConnection)


class TestConsumer(unittest.TestCase):

    def trigger(self):
        self.triggered = True

    def setUp(self):
        self.triggered = False
        
    def test_creation(self):
        consumer = Consumer(Request.ANY)

    def test_creation_wrong_arg(self):
        self.assertRaises(TypeError, Consumer, Request.ANY, wrong="wrong")

    def test_creation_requestChanged(self):
        consumer = Consumer(Request.ANY, requestChanged=lambda : None)

    def test_connection_requestChanged(self):
        consumer = Consumer(Request.ANY)
        consumer.requestChanged.connect(lambda : None)

    def test_request(self):
        consumer = Consumer(Request.ANY)
        self.assertEqual(consumer.request(), Request.ANY)

    def test_setRequest_raises(self):
        consumer = Consumer(Request.ANY)
        self.assertRaises(TypeError, consumer.setRequest, "wrong")

    def test_setRequest_different(self):
        consumer = Consumer(Request.ANY, requestChanged=self.trigger)
        consumer.setRequest(Request.NONE)
        self.assertEqual(consumer.request(), Request.NONE)
        self.assertTrue(self.triggered)

    def test_setRequest_equal(self):
        consumer = Consumer(Request.ANY)
        consumer.requestChanged.connect(self.trigger)
        consumer.setRequest(Request.ANY)
        self.assertEqual(consumer.request(), Request.ANY)
        self.assertFalse(self.triggered)

# -------------------------------------------------------------------

class Test_CustomerProducer(QtBasedTest):
        
    def production_test(self, mode):
        # Init Observers
        observer = Observer(react=testReact)
        # Consumers are set so that:
        # - the first is deleted during eventloop;
        # - the second won't get anything (request=None)
        # - the third will get only statues and paintings
        # - the fourth will get only statues
        consumers = []
        for request in (Request.ANY,
                        Request.NONE, 
                        eqRequestFactory("statue") + eqRequestFactory("painting"),
                        Request.ANY):
            consumers.append(Consumer(request, consume=storeProducts))
        reffirstconsumer = weakref.ref(consumers[0])
        # Init producer
        producer = _CustomerProducer(offer=Offer.UNDEFINED)
        QtCore.QTimer(
            producer, timeout=lambda : producer.postProduct("statue")).start(20)
        QtCore.QTimer(producer, timeout=lambda : self.assertFalse(
                producer.postProductTo("obelisk", observer))).start(30)
        QtCore.QTimer(producer, timeout=lambda : self.assertTrue(
                producer.postProductTo("painting", consumers[2]))).start(50)
        QtCore.QTimer(producer, timeout=lambda : self.assertFalse(
                producer.postProductTo("obelisk", consumers[2]))).start(60)
        # Subscriptions
        producer.addObserver(observer, mode)
        for consumer in consumers:
            producer.addObserver(consumer, mode)
        del consumer
        # Delete instances during eventloop
        setter = lambda obj, key, value: obj.__setitem__(key, value)
        QtCore.QTimer.singleShot(
            200, lambda : setter(consumers, 0, None))
        QtCore.QTimer.singleShot(
            300, self.app.quit)
        # Exec
        self.app.exec_()
        # Check element deletion
        self.assertIsNone(reffirstconsumer())
        self.assertEqual(set(producer.observers()), 
                         set(itertools.chain(consumers[1:], 
                                             (observer, ))))
        # Check react func
        self.assertGreater(observer.hit, 0)
        self.assertFalse(hasattr(consumers[1], "storage"))
        self.assertIn("statue", consumers[2].storage)
        self.assertIn("painting", consumers[2].storage)
        self.assertNotIn("obelisk", consumers[2].storage)
        self.assertIn("statue", consumers[3].storage)
        self.assertNotIn("painting", consumers[3].storage)
        self.assertNotIn("obelisk", consumers[3].storage)

    def test_production_direct(self):
        self.production_test(QtCore.Qt.DirectConnection)

    def test_production_queued(self):
        self.production_test(QtCore.Qt.QueuedConnection)

# -------------------------------------------------------------------

def suite():    
    testcases = (
        TestRequest,
        TestFunctorRequest,
        Test_CompositeRequest,
        TestProducer,
        TestConsumer,
        Test_CustomerProducer,
        )
    return unittest.TestSuite(itertools.chain(
            *(map(t, filter(lambda f: f.startswith("test_"), dir(t))) \
                  for t in testcases)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
