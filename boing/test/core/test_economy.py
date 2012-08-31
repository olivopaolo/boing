#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# boing/test/core/test_economy.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import itertools
import unittest
import weakref

from PyQt4 import QtCore

from boing.core.economy import \
    Offer, Request, LambdaRequest, \
    Producer, Consumer, BaseWorker, \
    Composite, CompositeProducer, CompositeConsumer, CompositeWorker
from boing.core.observer import Observer
from boing.test import QtBasedTest
from boing.test.core.test_observer import testReact

class TestingConfigurableConsumer(Consumer, Consumer.ConfigurableRequest):
    pass

class TestRequest(unittest.TestCase):

    def setUp(self):
        self.request = LambdaRequest(lambda product: bool(product))

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

class TestLambdaRequest(unittest.TestCase):

    def setUp(self):
        self.functor = lambda product: bool(product)

    def test_creation_raises(self):
        self.assertRaises(TypeError, LambdaRequest, "wrong")

    def test_test(self):
        request = LambdaRequest(self.functor)
        self.assertTrue(request.test(True))
        self.assertFalse(request.test(False))

    def test_equal(self):
        self.assertEqual(LambdaRequest(self.functor),
                         LambdaRequest(self.functor))

    def test_hash(self):
        hash(LambdaRequest(self.functor))


class Test_CompositeRequest(unittest.TestCase):

    def setUp(self):
        self.truerequest = LambdaRequest(
            lambda product: bool(product))
        self.tuplerequest = LambdaRequest(
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
    return LambdaRequest(lambda product: product==other)

def storeProducts(consumer, products, producer):
    storage = consumer.__dict__.setdefault("storage", list())
    storage.extend(products)

class TestProducer(QtBasedTest):

    # FIXME: Add tag tests

    def test_creation(self):
        producer = Producer(offer=Offer(Offer.UNDEFINED))
        ref = weakref.ref(producer)
        del producer
        self.assertIsNone(ref())

    def test_creation_wrong_arg(self):
        self.assertRaises(TypeError, Producer, wrong="wrong")

    def test_connect_demandChanged(self):
        producer = Producer(offer=Offer(Offer.UNDEFINED))
        producer.demandChanged.connect(lambda : None)

    def test_connect_demandedOfferChanged(self):
        producer = Producer(offer=Offer(Offer.UNDEFINED))
        producer.demandedOfferChanged.connect(lambda : None)

    def test_offer(self):
        producer = Producer(offer=Offer(Offer.UNDEFINED))
        self.assertEqual(producer.offer(), Offer(Offer.UNDEFINED))
        offer = Offer("statue", "painting")
        producer = Producer(offer=offer)
        self.assertEqual(producer.offer(), offer)
        self.assertNotEqual(producer.offer(), Offer("obelisk"))
        self.assertNotEqual(producer.offer(), Offer("statue"))

    def test_meetsRequest(self):
        producer = Producer(offer=Offer(Offer.UNDEFINED))
        self.assertTrue(producer.meetsRequest(eqRequestFactory("statue")))
        self.assertTrue(producer.meetsRequest(Request.ANY))
        producer = Producer(Offer("statue", "obelisk"))
        self.assertTrue(producer.meetsRequest(eqRequestFactory("statue")))
        self.assertTrue(producer.meetsRequest(Request.ANY))
        self.assertFalse(producer.meetsRequest(eqRequestFactory("painting")))
        self.assertTrue(producer.meetsRequest(
                eqRequestFactory("statue")+eqRequestFactory("obelisk")))

    def test_addObservers(self):
        producer = Producer(offer=Offer(Offer.UNDEFINED))
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
        producer = Producer(offer=Offer("statue", "painting", "obelisk"))
        producer.demandChanged.connect(
            lambda : setattr(self, "demandTrigger", True))
        producer.demandedOfferChanged.connect(
            lambda : setattr(self, "offerTrigger", True))
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
            producers.append(Producer(Offer(Offer.UNDEFINED)))
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
            consumers.append(
                TestingConfigurableConsumer(request, consume=storeProducts))
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

    def test__add__None(self):
        # prod + None = prod
        prod = Producer(Offer())
        self.assertEqual(prod+None, prod)

    def test__radd__None(self):
        # None + prod = prod
        prod = Producer(Offer())
        self.assertEqual(None+prod, prod)

    def test__add__Producer(self):
        # prod + prod => Exception
        prod = Producer(Offer())
        try: prod + Producer(Offer())
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__Consumer(self):
        # prod + cons => Composite
        prod = Producer(Offer())
        cons = Consumer(Request.ANY)
        result = prod + cons
        self.assertIsInstance(result, Composite)
        self.assertEqual(set(result.internals()), {prod, cons})
        self.assertEqual(set(prod.observers()), {cons})
        self.assertEqual(set(cons.observed()), {prod})

    def test__add__Worker(self):
        # prod + worker => CompositeProducer
        prod = Producer(Offer())
        worker = BaseWorker(Request.ANY, Offer())
        result = prod + worker
        self.assertIsInstance(result, CompositeProducer)
        self.assertEqual(set(result.producers()), {worker})
        self.assertEqual(set(result.internals()), {prod, worker})
        self.assertEqual(set(prod.observers()), {worker})
        self.assertEqual(set(worker.observed()), {prod})
        self.assertEqual(len(set(worker.observers())), 1)

    def test__add__Composite(self):
        # prod + composite => Exception
        prod = Producer(Offer())
        try: prod + (Producer(Offer()) + Consumer(Request.ANY))
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__CompositeProducer(self):
        # prod + composite => Exception
        prod = Producer(Offer())
        composite = Producer(Offer()) + BaseWorker(Request.ANY, Offer())
        try: prod + composite
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__CompositeConsumer(self):
        # prod + composite => Composite
        prod = Producer(Offer())
        worker = BaseWorker(Request.ANY, Offer())
        cons = Consumer(Request.ANY)
        result = prod + (worker + cons)
        self.assertIsInstance(result, Composite)
        self.assertEqual(set(result.internals()), {prod, worker, cons})
        self.assertEqual(set(prod.observers()), {worker})
        self.assertEqual(set(worker.observed()), {prod})
        self.assertEqual(set(worker.observers()), {cons})
        self.assertEqual(set(cons.observed()), {worker})

    def test__add__CompositeWorker(self):
        # prod + composite => Composite
        prod = Producer(Offer())
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        result = prod + (worker + worker2)
        self.assertIsInstance(result, CompositeProducer)
        self.assertEqual(set(result.internals()), {prod, worker, worker2})
        self.assertEqual(set(prod.observers()), {worker})
        self.assertEqual(set(worker.observed()), {prod})
        self.assertEqual(set(worker.observers()), {worker2})
        self.assertEqual(set(worker2.observed()), {worker})
        self.assertEqual(len(set(worker2.observers())), 1)

    def test__or__None(self):
        prod = Producer(Offer())
        # prod | None = prod
        self.assertEqual(prod|None, prod)

    def test__ror__None(self):
        prod = Producer(Offer())
        # None | prod = prod
        self.assertEqual(None|prod, prod)

    def test__or__Producer(self):
        # prod | prod2 => CompositeProducer(prod, prod2)
        prod = Producer(Offer())
        prod2 = Producer(Offer())
        result = prod | prod2
        self.assertIsInstance(result, CompositeProducer)
        self.assertEqual(set(result.producers()), {prod, prod2})
        self.assertEqual(set(result.internals()), {prod, prod2})
        self.assertEqual(len(set(prod.observers())), 1)
        self.assertEqual(len(set(prod2.observers())), 1)

    def test__or__Consumer(self):
        # prod | cons => Exception
        prod = Producer(Offer())
        try: prod | Consumer(Request.NONE)
        except TypeError: pass
        else: self.fail("TypeError not raised by __or__")

    def test__or__Worker(self):
        # prod | worker => CompositeWorker
        prod = Producer(Offer())
        worker = BaseWorker(Request.ANY, Offer())
        result = prod | worker
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.producers()), {prod, worker})
        self.assertEqual(set(result.consumers()), {worker})
        self.assertEqual(set(result.internals()), {prod, worker})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(len(set(prod.observers())), 1)
        self.assertEqual(len(set(worker.observers())), 1)

    def test__or__CompositeProducer(self):
        # prod | composite => CompositeProducer
        prod = Producer(Offer())
        prod2 = Producer(Offer())
        prod3 = Producer(Offer())
        result = prod | (prod2 | prod3)
        self.assertIsInstance(result, CompositeProducer)
        self.assertEqual(set(result.producers()), {prod, prod2, prod3})
        self.assertEqual(set(result.internals()), {prod, prod2, prod3})
        self.assertEqual(len(set(prod.observers())), 1)
        self.assertEqual(len(set(prod2.observers())), 1)
        self.assertEqual(len(set(prod3.observers())), 1)

    def test__or_CompositeConsumer(self):
        # prod | composite => Exception
        prod = Producer(Offer())
        try: prod | (Consumer(Request.NONE) | Consumer(Request.NONE))
        except TypeError: pass
        else: self.fail("TypeError not raised by __or__")

    def test__or_CompositeWorker(self):
        # prod | composite => CompositeWorker
        prod = Producer(Offer())
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        result = prod | (worker|worker2)
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.producers()), {prod, worker, worker2})
        self.assertEqual(set(result.consumers()), {worker, worker2})
        self.assertEqual(set(result.internals()), {prod, worker, worker2})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(len(set(worker2.observed())), 1)
        self.assertEqual(len(set(prod.observers())), 1)
        self.assertEqual(len(set(worker.observers())), 1)
        self.assertEqual(len(set(worker2.observers())), 1)


class TestConsumer(unittest.TestCase):

    def trigger(self):
        self.triggered = True

    def setUp(self):
        self.triggered = False

    def test_creation(self):
        consumer = Consumer(Request.ANY)

    def test_creation_wrong_arg(self):
        self.assertRaises(TypeError, Consumer, Request.ANY, wrong="wrong")

    def test_connection_requestChanged(self):
        consumer = Consumer(Request.ANY)
        consumer.requestChanged.connect(lambda : None)

    def test_request(self):
        consumer = Consumer(Request.ANY)
        self.assertEqual(consumer.request(), Request.ANY)

    def test__add__None(self):
        # cons + None = cons
        cons = Consumer(Request.ANY)
        self.assertEqual(cons+None, cons)

    def test__radd__None(self):
        # None + cons = cons
        cons = Consumer(Request.ANY)
        self.assertEqual(None+cons, cons)

    def test__add__Producer(self):
        # cons + prod => Exception
        cons = Consumer(Request.ANY)
        try: cons + Producer(Offer())
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__Consumer(self):
        # cons + cons => Exception
        cons = Consumer(Request.ANY)
        try: cons + Consumer(Request.ANY)
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__Worker(self):
        # cons + worker => Exception
        cons = Consumer(Request.ANY)
        try: cons + BaseWorker(Request.ANY, Offer())
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__Composite(self):
        # cons + composite => Exception
        cons = Consumer(Request.ANY)
        composite = Producer(Offer())+Consumer(Request.ANY)
        try: cons + composite
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__CompositeProducer(self):
        # cons + composite => Exception
        cons = Consumer(Request.ANY)
        composite = Producer(Offer())+BaseWorker(Request.ANY, Offer())
        try: cons + composite
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__CompositeConsumer(self):
        # cons + composite => Exception
        cons = Consumer(Request.ANY)
        composite = BaseWorker(Request.ANY, Offer())+Consumer(Request.ANY)
        try: cons + composite
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__CompositeWorker(self):
        # cons + composite => Exception
        cons = Consumer(Request.ANY)
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        composite = worker + worker2
        try: cons + composite
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__or__None(self):
        cons = Consumer(Request.ANY)
        # cons | None = cons
        self.assertEqual(cons|None, cons)

    def test__ror__None(self):
        cons = Consumer(Request.ANY)
        # None | cons = cons
        self.assertEqual(None|cons, cons)

    def test__or__Producer(self):
        # cons | prod => Exception
        cons = Consumer(Request.ANY)
        try: cons | Producer(Offer())
        except TypeError: pass
        else: self.fail("TypeError not raised by __or__")

    def test__or__Consumer(self):
        # cons | cons2 => CompositeConsumer(cons, cons2)
        cons = Consumer(Request.ANY)
        cons2 = Consumer(Request.ANY)
        result = cons | cons2
        self.assertIsInstance(result, CompositeConsumer)
        self.assertEqual(set(result.consumers()), {cons, cons2})
        self.assertEqual(set(result.internals()), {cons, cons2})
        self.assertEqual(len(set(cons.observed())), 1)
        self.assertEqual(len(set(cons2.observed())), 1)

    def test__or__Worker(self):
        # cons | worker => CompositeWorker
        cons = Consumer(Request.ANY)
        worker = BaseWorker(Request.ANY, Offer())
        result = cons | worker
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.consumers()), {cons, worker})
        self.assertEqual(set(result.producers()), {worker})
        self.assertEqual(set(result.internals()), {cons, worker})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(len(set(cons.observed())), 1)
        self.assertEqual(len(set(worker.observers())), 1)

    def test__or__CompositeProducer(self):
        # cons | composite => Exception
        cons = Consumer(Request.ANY)
        try: cons | (Producer(Offer()) | Producer(Offer()))
        except TypeError: pass
        else: self.fail("TypeError not raised by __or__")

    def test__or_CompositeConsumer(self):
        # cons | composite => CompositeConsumer
        cons = Consumer(Request.ANY)
        cons2 = Consumer(Request.ANY)
        cons3 = Consumer(Request.ANY)
        result = cons | (cons2 | cons3)
        self.assertIsInstance(result, CompositeConsumer)
        self.assertEqual(set(result.consumers()), {cons, cons2, cons3})
        self.assertEqual(set(result.internals()), {cons, cons2, cons3})
        self.assertEqual(len(set(cons.observed())), 1)
        self.assertEqual(len(set(cons2.observed())), 1)
        self.assertEqual(len(set(cons3.observed())), 1)

    def test__or_CompositeWorker(self):
        # cons | composite => CompositeWorker
        cons = Consumer(Request.ANY)
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        result = cons | (worker|worker2)
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.consumers()), {cons, worker, worker2})
        self.assertEqual(set(result.producers()), {worker, worker2})
        self.assertEqual(set(result.internals()), {cons, worker, worker2})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(len(set(worker2.observed())), 1)
        self.assertEqual(len(set(cons.observed())), 1)
        self.assertEqual(len(set(worker.observers())), 1)
        self.assertEqual(len(set(worker2.observers())), 1)


class TestConfigurableConsumer(unittest.TestCase):

    def trigger(self):
        self.triggered = True

    def setUp(self):
        self.triggered = False

    def test_setRequest_raises(self):
        consumer = TestingConfigurableConsumer(Request.ANY)
        self.assertRaises(TypeError, consumer.setRequest, "wrong")

    def test_setRequest_different(self):
        consumer = TestingConfigurableConsumer(Request.ANY)
        consumer.requestChanged.connect(self.trigger)
        consumer.setRequest(Request.NONE)
        self.assertEqual(consumer.request(), Request.NONE)
        self.assertTrue(self.triggered)

    def test_setRequest_equal(self):
        consumer = TestingConfigurableConsumer(Request.ANY)
        consumer.requestChanged.connect(self.trigger)
        consumer.setRequest(Request.ANY)
        self.assertEqual(consumer.request(), Request.ANY)
        self.assertFalse(self.triggered)


class TestBaseWorker(unittest.TestCase):

    def test__add__None(self):
        # worker + None = worker
        worker = BaseWorker(Request.ANY, Offer())
        self.assertEqual(worker+None, worker)

    def test__radd__None(self):
        # None + worker = worker
        worker = BaseWorker(Request.ANY, Offer())
        self.assertEqual(None+worker, worker)

    def test__add__Producer(self):
        # worker + producer => Exception
        worker = BaseWorker(Request.ANY, Offer())
        try: worker + Producer(Offer())
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__Consumer(self):
        # worker + cons => CompositeConsumer
        worker = BaseWorker(Request.ANY, Offer())
        cons = Consumer(Request.ANY)
        result = worker + cons
        self.assertIsInstance(result, CompositeConsumer)
        self.assertEqual(set(result.consumers()), {worker})
        self.assertEqual(set(result.internals()), {worker, cons})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(set(worker.observers()), {cons})
        self.assertEqual(set(cons.observed()), {worker})

    def test__add__Worker(self):
        # worker + worker => CompositeWorker
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        result = worker + worker2
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.producers()), {worker2})
        self.assertEqual(set(result.consumers()), {worker})
        self.assertEqual(set(result.internals()), {worker, worker2})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(set(worker.observers()), {worker2})
        self.assertEqual(set(worker2.observed()), {worker})
        self.assertEqual(len(set(worker.observers())), 1)

    def test__add__Composite(self):
        # worker + composite => Exception
        worker = BaseWorker(Request.ANY, Offer())
        composite = Producer(Offer()) + Consumer(Request.ANY)
        try: worker + composite
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__CompositeProducer(self):
        # worker + composite => Exception
        worker = BaseWorker(Request.ANY, Offer())
        composite = Producer(Offer()) + BaseWorker(Request.ANY, Offer())
        try: worker + composite
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__CompositeConsumer(self):
        # worker + composite => CompositeConsumer
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        cons = Consumer(Request.ANY)
        result = worker + (worker2 + cons)
        self.assertIsInstance(result, CompositeConsumer)
        self.assertEqual(set(result.consumers()), {worker})
        self.assertEqual(set(result.internals()), {worker, worker2, cons})
        self.assertEqual(set(worker.observers()), {worker2})
        self.assertEqual(set(worker2.observed()), {worker})
        self.assertEqual(set(worker2.observers()), {cons})
        self.assertEqual(set(cons.observed()), {worker2})

    def test__add__CompositeWorker(self):
        # worker + composite => CompositeConsumer
        worker = BaseWorker(Request.ANY, Offer())
        worker2 =BaseWorker(Request.ANY, Offer())
        worker3 =BaseWorker(Request.ANY, Offer())
        result = worker + (worker2 + worker3)
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.consumers()), {worker})
        self.assertEqual(set(result.producers()), {worker3})
        self.assertEqual(set(result.internals()), {worker, worker2, worker3})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(set(worker.observers()), {worker2})
        self.assertEqual(set(worker2.observed()), {worker})
        self.assertEqual(set(worker2.observers()), {worker3})
        self.assertEqual(set(worker3.observed()), {worker2})
        self.assertEqual(len(set(worker3.observers())), 1)

    def test__or__None(self):
        worker = BaseWorker(Request.ANY, Offer())
        # worker | None = worker
        self.assertEqual(worker|None, worker)

    def test__ror__None(self):
        worker = BaseWorker(Request.ANY, Offer())
        # None | worker = worker
        self.assertEqual(None|worker, worker)

    def test__or__Producer(self):
        # worker | prod => CompositeWorker
        worker = BaseWorker(Request.ANY, Offer())
        prod = Producer(Offer())
        result = worker | prod
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.producers()), {prod, worker})
        self.assertEqual(set(result.consumers()), {worker})
        self.assertEqual(set(result.internals()), {prod, worker})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(len(set(prod.observers())), 1)
        self.assertEqual(len(set(worker.observers())), 1)

    def test__or__Consumer(self):
        # worker | cons => CompositeWorker
        worker = BaseWorker(Request.ANY, Offer())
        cons = Consumer(Request.ANY)
        result = worker | cons
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.consumers()), {cons, worker})
        self.assertEqual(set(result.producers()), {worker})
        self.assertEqual(set(result.internals()), {cons, worker})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(len(set(cons.observed())), 1)
        self.assertEqual(len(set(worker.observers())), 1)

    def test__or__Worker(self):
        # worker | worker2 => CompositeWorker
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        result = worker | worker2
        self.assertEqual(set(result.consumers()), {worker, worker2})
        self.assertEqual(set(result.producers()), {worker, worker2})
        self.assertEqual(set(result.internals()), {worker, worker2})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(len(set(worker2.observed())), 1)
        self.assertEqual(len(set(worker.observers())), 1)
        self.assertEqual(len(set(worker2.observers())), 1)

    def test__or__CompositeProducer(self):
        # worker | prod => CompositeWorker
        worker = BaseWorker(Request.ANY, Offer())
        prod = Producer(Offer())
        prod2 = Producer(Offer())
        result = worker | (prod | prod2)
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.producers()), {prod, prod2, worker})
        self.assertEqual(set(result.consumers()), {worker})
        self.assertEqual(set(result.internals()), {prod, prod2, worker})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(len(set(prod.observers())), 1)
        self.assertEqual(len(set(prod2.observers())), 1)
        self.assertEqual(len(set(worker.observers())), 1)

    def test__or_CompositeConsumer(self):
        # worker | composite => CompositeWorker
        worker = BaseWorker(Request.ANY, Offer())
        cons = Consumer(Request.ANY)
        cons2 = Consumer(Request.ANY)
        result = worker | (cons | cons2)
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.consumers()), {cons, cons2, worker})
        self.assertEqual(set(result.producers()), {worker})
        self.assertEqual(set(result.internals()), {cons, cons2, worker})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(len(set(cons.observed())), 1)
        self.assertEqual(len(set(cons2.observed())), 1)
        self.assertEqual(len(set(worker.observers())), 1)

    def test__or_CompositeWorker(self):
        # worker | composite => CompositeWorker
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        worker3 = BaseWorker(Request.ANY, Offer())
        result = worker | (worker2|worker3)
        self.assertEqual(set(result.consumers()), {worker, worker2, worker3})
        self.assertEqual(set(result.producers()), {worker, worker2, worker3})
        self.assertEqual(set(result.internals()), {worker, worker2, worker3})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(len(set(worker2.observed())), 1)
        self.assertEqual(len(set(worker3.observed())), 1)
        self.assertEqual(len(set(worker.observers())), 1)
        self.assertEqual(len(set(worker2.observers())), 1)
        self.assertEqual(len(set(worker3.observers())), 1)


class TestCompositeProducer(unittest.TestCase):

    def test__add__None(self):
        # composite + None = composite
        prod = Producer(Offer())
        worker = BaseWorker(Request.ANY, Offer())
        composite = prod + worker
        self.assertEqual(composite+None, composite)

    def test__radd__None(self):
        # None + composite = composite
        prod = Producer(Offer())
        worker = BaseWorker(Request.ANY, Offer())
        composite = prod + worker
        self.assertEqual(None+composite, composite)

    def test__add__Producer(self):
        # composite + prod => Exception
        prod = Producer(Offer())
        worker = BaseWorker(Request.ANY, Offer())
        composite = prod + worker
        try: composite + Producer(Offer())
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__Consumer(self):
        # composite + cons => Composite
        prod = Producer(Offer())
        worker = BaseWorker(Request.ANY, Offer())
        cons = Consumer(Request.ANY)
        result = (prod + worker) + cons
        self.assertIsInstance(result, Composite)
        self.assertEqual(set(result.internals()), {prod, worker, cons})
        self.assertEqual(set(prod.observers()), {worker})
        self.assertEqual(set(worker.observed()), {prod})
        self.assertEqual(set(worker.observers()), {cons})
        self.assertEqual(set(cons.observed()), {worker})

    def test__add__Worker(self):
        # composite + worker => CompositeProducer
        prod = Producer(Offer())
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        result = (prod + worker) + worker2
        self.assertIsInstance(result, CompositeProducer)
        self.assertEqual(set(result.producers()), {worker2})
        self.assertEqual(set(result.internals()), {prod, worker, worker2})
        self.assertEqual(set(prod.observers()), {worker})
        self.assertEqual(set(worker.observed()), {prod})
        self.assertEqual(set(worker.observers()), {worker2})
        self.assertEqual(set(worker2.observed()), {worker})
        self.assertEqual(len(set(worker2.observers())), 1)

    def test__add__Composite(self):
        # composite + composite => Exception
        prod = Producer(Offer())
        worker = BaseWorker(Request.ANY, Offer())
        composite = prod + worker
        try: composite + (Producer(Offer()) + Consumer(Request.ANY))
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__CompositeProducer(self):
        # composite + composite => Exception
        prod = Producer(Offer())
        worker = BaseWorker(Request.ANY, Offer())
        composite = prod + worker
        composite2 = Producer(Offer()) + BaseWorker(Request.ANY, Offer())
        try: composite + composite2
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__CompositeConsumer(self):
        # composite + composite => Composite
        prod = Producer(Offer())
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        cons = Consumer(Request.ANY)
        result =  (prod + worker) + (worker2 + cons)
        self.assertIsInstance(result, Composite)
        self.assertEqual(set(result.internals()), {prod, worker, worker2, cons})
        self.assertEqual(set(prod.observers()), {worker})
        self.assertEqual(set(worker.observed()), {prod})
        self.assertEqual(set(worker.observers()), {worker2})
        self.assertEqual(set(worker2.observed()), {worker})
        self.assertEqual(set(worker2.observers()), {cons})
        self.assertEqual(set(cons.observed()), {worker2})

    def test__add__CompositeWorker(self):
        # composite + composite => Composite
        prod = Producer(Offer())
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        worker3 = BaseWorker(Request.ANY, Offer())
        compprod = (prod + worker)
        compworker = (worker2 + worker3)
        result = compprod + compworker
        del compprod, compworker
        self.assertIsInstance(result, CompositeProducer)
        self.assertEqual(set(result.internals()), {prod, worker, worker2, worker3})
        self.assertEqual(set(prod.observers()), {worker})
        self.assertEqual(set(worker.observed()), {prod})
        self.assertEqual(set(worker.observers()), {worker2})
        self.assertEqual(set(worker2.observed()), {worker})
        self.assertEqual(set(worker2.observers()), {worker3})
        self.assertEqual(set(worker3.observed()), {worker2})
        self.assertEqual(len(set(worker3.observers())), 1)

    def test__or__None(self):
        # composite | None = composite
        composite = Producer(Offer()) | Producer(Offer())
        self.assertEqual(composite|None, composite)

    def test__ror__None(self):
        composite = Producer(Offer()) | Producer(Offer())
        # None | composite = composite
        self.assertEqual(None|composite, composite)

    def test__or__Producer(self):
        # composite | prod => CompositeProducer
        prod = Producer(Offer())
        prod2 = Producer(Offer())
        prod3 = Producer(Offer())
        result = (prod | prod2) | prod3
        self.assertIsInstance(result, CompositeProducer)
        self.assertEqual(set(result.producers()), {prod, prod2, prod3})
        self.assertEqual(set(result.internals()), {prod, prod2, prod3})
        self.assertEqual(len(set(prod.observers())), 1)
        self.assertEqual(len(set(prod2.observers())), 1)
        self.assertEqual(len(set(prod3.observers())), 1)

    def test__or__Consumer(self):
        # composite | cons => Exception
        composite = Producer(Offer()) | Producer(Offer())
        try: composite | Consumer(Request.NONE)
        except TypeError: pass
        else: self.fail("TypeError not raised by __or__")

    def test__or__Worker(self):
        # composite | worker => CompositeWorker
        prod = Producer(Offer())
        prod2 = Producer(Offer())
        worker = BaseWorker(Request.ANY, Offer())
        result = (prod | prod2) | worker
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.producers()), {prod, prod2, worker})
        self.assertEqual(set(result.consumers()), {worker})
        self.assertEqual(set(result.internals()), {prod, prod2, worker})
        self.assertEqual(len(set(prod.observers())), 1)
        self.assertEqual(len(set(prod2.observers())), 1)
        self.assertEqual(len(set(worker.observers())), 1)
        self.assertEqual(len(set(worker.observed())), 1)

    def test__or__CompositeProducer(self):
        # composite | composite => CompositeProducer
        prod = Producer(Offer())
        prod2 = Producer(Offer())
        prod3 = Producer(Offer())
        prod4 = Producer(Offer())
        result = (prod | prod2) | (prod3 | prod4)
        self.assertIsInstance(result, CompositeProducer)
        self.assertEqual(set(result.producers()), {prod, prod2, prod3, prod4})
        self.assertEqual(set(result.internals()), {prod, prod2, prod3, prod4})
        self.assertEqual(len(set(prod.observers())), 1)
        self.assertEqual(len(set(prod2.observers())), 1)
        self.assertEqual(len(set(prod3.observers())), 1)
        self.assertEqual(len(set(prod4.observers())), 1)

    def test__or_CompositeConsumer(self):
        # composite | composite => Exception
        composite = Producer(Offer()) | Producer(Offer())
        try: composite | (Consumer(Request.NONE) | Consumer(Request.NONE))
        except TypeError: pass
        else: self.fail("TypeError not raised by __or__")

    def test__or_CompositeWorker(self):
        # composite | composite => CompositeWorker
        prod = Producer(Offer())
        prod2 = Producer(Offer())
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        result = (prod | prod2) | (worker|worker2)
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.producers()), {prod, prod2, worker, worker2})
        self.assertEqual(set(result.consumers()), {worker, worker2})
        self.assertEqual(set(result.internals()), {prod, prod2, worker, worker2})
        self.assertEqual(len(set(prod.observers())), 1)
        self.assertEqual(len(set(prod2.observers())), 1)
        self.assertEqual(len(set(worker.observers())), 1)
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(len(set(worker2.observers())), 1)
        self.assertEqual(len(set(worker2.observed())), 1)


class TestCompositeConsumer(unittest.TestCase):

    def test__add__None(self):
        # composite + None = composite
        worker = BaseWorker(Request.ANY, Offer())
        cons = Consumer(Request.ANY)
        composite = worker + cons
        self.assertEqual(composite+None, composite)

    def test__radd__None(self):
        # None + composite = composite
        worker = BaseWorker(Request.ANY, Offer())
        cons= Consumer(Request.ANY)
        composite = worker + cons
        self.assertEqual(None+composite, composite)

    def test__add__Producer(self):
        # composite + prod => Exception
        worker = BaseWorker(Request.ANY, Offer())
        cons= Consumer(Request.ANY)
        composite = worker + cons
        try: composite + Producer(Offer())
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__Consumer(self):
        # composite + cons => Exception
        worker = BaseWorker(Request.ANY, Offer())
        cons= Consumer(Request.ANY)
        composite = worker + cons
        try: composite + Consumer(Request.ANY)
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__Worker(self):
        # composite + worker => Exception
        worker = BaseWorker(Request.ANY, Offer())
        cons= Consumer(Request.ANY)
        composite = worker + cons
        try: composite + BaseWorker(Request.ANY, Offer())
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__Composite(self):
        # composite + composite => Exception
        worker = BaseWorker(Request.ANY, Offer())
        cons= Consumer(Request.ANY)
        composite = worker + cons
        composite2 = Producer(Offer())+Consumer(Request.ANY)
        try: composite + composite2
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__CompositeProducer(self):
        # composite + composite => Exception
        worker = BaseWorker(Request.ANY, Offer())
        cons= Consumer(Request.ANY)
        composite = worker + cons
        composite2 = Producer(Offer())+BaseWorker(Request.ANY, Offer())
        try: composite + composite2
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__CompositeConsumer(self):
        # composite + composite => Exception
        worker = BaseWorker(Request.ANY, Offer())
        cons= Consumer(Request.ANY)
        composite = worker + cons
        composite2 = BaseWorker(Request.ANY, Offer())+Consumer(Request.ANY)
        try: composite + composite2
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__CompositeWorker(self):
        # composite + composite => Exception
        worker = BaseWorker(Request.ANY, Offer())
        cons= Consumer(Request.ANY)
        composite = worker + cons
        worker2 = BaseWorker(Request.ANY, Offer())
        worker3 = BaseWorker(Request.ANY, Offer())
        composite2 = worker2 + worker3
        try: composite + composite2
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__or__None(self):
        composite = Consumer(Request.ANY) | Consumer(Request.ANY)
        # composite | None = composite
        self.assertEqual(composite|None, composite)

    def test__ror__None(self):
        composite = Consumer(Request.ANY) | Consumer(Request.ANY)
        # None | composite = composite
        self.assertEqual(None|composite, composite)

    def test__or__Producer(self):
        # composite | prod => Exception
        composite = Consumer(Request.ANY) | Consumer(Request.ANY)
        try: composite | Producer(Offer())
        except TypeError: pass
        else: self.fail("TypeError not raised by __or__")

    def test__or__Consumer(self):
        # composite | cons2 => CompositeConsumer(composite, cons2)
        cons = Consumer(Request.ANY)
        cons2 = Consumer(Request.ANY)
        cons3 = Consumer(Request.ANY)
        result = (cons | cons2) | cons3
        self.assertIsInstance(result, CompositeConsumer)
        self.assertEqual(set(result.consumers()), {cons, cons2, cons3})
        self.assertEqual(set(result.internals()), {cons, cons2, cons3})
        self.assertEqual(len(set(cons.observed())), 1)
        self.assertEqual(len(set(cons2.observed())), 1)
        self.assertEqual(len(set(cons3.observed())), 1)

    def test__or__Worker(self):
        # cons | worker => CompositeWorker
        cons = Consumer(Request.ANY)
        worker = BaseWorker(Request.ANY, Offer())
        result = cons | worker
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.consumers()), {cons, worker})
        self.assertEqual(set(result.producers()), {worker})
        self.assertEqual(set(result.internals()), {cons, worker})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(len(set(cons.observed())), 1)
        self.assertEqual(len(set(worker.observers())), 1)

    def test__or__CompositeProducer(self):
        # cons | composite => Exception
        cons = Consumer(Request.ANY)
        try: cons | (Producer(Offer()) | Producer(Offer()))
        except TypeError: pass
        else: self.fail("TypeError not raised by __or__")

    def test__or__CompositeConsumer(self):
        # composite | composite => CompositeConsumer
        cons = Consumer(Request.ANY)
        cons2 = Consumer(Request.ANY)
        cons3 = Consumer(Request.ANY)
        cons4 = Consumer(Request.ANY)
        result = (cons | cons2) | (cons3 | cons4)
        self.assertIsInstance(result, CompositeConsumer)
        self.assertEqual(set(result.consumers()), {cons, cons2, cons3, cons4})
        self.assertEqual(set(result.internals()), {cons, cons2, cons3, cons4})
        self.assertEqual(len(set(cons.observed())), 1)
        self.assertEqual(len(set(cons2.observed())), 1)
        self.assertEqual(len(set(cons3.observed())), 1)
        self.assertEqual(len(set(cons4.observed())), 1)

    def test__or__CompositeWorker(self):
        # cons | worker => CompositeWorker
        cons = Consumer(Request.ANY)
        cons2 = Consumer(Request.ANY)
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        result = (cons | cons2) | (worker | worker2)
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.consumers()), {cons, cons2, worker, worker2})
        self.assertEqual(set(result.producers()), {worker, worker2})
        self.assertEqual(set(result.internals()), {cons, cons2, worker, worker2})
        self.assertEqual(len(set(cons.observed())), 1)
        self.assertEqual(len(set(cons2.observed())), 1)
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(len(set(worker2.observed())), 1)
        self.assertEqual(len(set(worker.observers())), 1)
        self.assertEqual(len(set(worker2.observers())), 1)


class TestCompositeWorker(unittest.TestCase):

    def test__add__None(self):
        # composite + None = composite
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        composite = worker + worker2
        self.assertEqual(composite+None, composite)

    def test__radd__None(self):
        # None + composite = composite
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        composite = worker + worker2
        self.assertEqual(None+composite, composite)

    def test__add__Producer(self):
        # composite + producer => Exception
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        composite = worker + worker2
        try: composite + Producer(Offer())
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__Consumer(self):
        # composite + cons => CompositeConsumer
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        cons = Consumer(Request.ANY)
        result = (worker + worker2) + cons
        self.assertIsInstance(result, CompositeConsumer)
        self.assertEqual(set(result.consumers()), {worker})
        self.assertEqual(set(result.internals()), {worker, worker2, cons})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(set(worker.observers()), {worker2})
        self.assertEqual(set(worker2.observed()), {worker})
        self.assertEqual(set(worker2.observers()), {cons})
        self.assertEqual(set(cons.observed()), {worker2})

    def test__add__Worker(self):
        # composite + worker => CompositeWorker
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        worker3 = BaseWorker(Request.ANY, Offer())
        result = (worker + worker2) + worker3
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.consumers()), {worker})
        self.assertEqual(set(result.producers()), {worker3})
        self.assertEqual(set(result.internals()), {worker, worker2, worker3})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(set(worker.observers()), {worker2})
        self.assertEqual(set(worker2.observed()), {worker})
        self.assertEqual(set(worker2.observers()), {worker3})
        self.assertEqual(set(worker3.observed()), {worker2})
        self.assertEqual(len(set(worker3.observers())), 1)

    def test__add__Composite(self):
        # composite + composite => Exception
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        composite = worker + worker2
        composite2 = Producer(Offer()) + Consumer(Request.ANY)
        try: composite + composite2
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__CompositeProducer(self):
        # composite + composite => Exception
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        composite = worker + worker2
        composite2 = Producer(Offer()) + BaseWorker(Request.ANY, Offer())
        try: composite + composite2
        except TypeError: pass
        else: self.fail("TypeError not raised by __add__")

    def test__add__CompositeConsumer(self):
        # composite + cons => CompositeConsumer
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        worker3 = BaseWorker(Request.ANY, Offer())
        cons = Consumer(Request.ANY)
        result = (worker + worker2) + (worker3 + cons)
        self.assertIsInstance(result, CompositeConsumer)
        self.assertEqual(set(result.consumers()), {worker})
        self.assertEqual(set(result.internals()), {worker, worker2, worker3, cons})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(set(worker.observers()), {worker2})
        self.assertEqual(set(worker2.observed()), {worker})
        self.assertEqual(set(worker2.observers()), {worker3})
        self.assertEqual(set(worker3.observed()), {worker2})
        self.assertEqual(set(worker3.observers()), {cons})
        self.assertEqual(set(cons.observed()), {worker3})

    def test__add__CompositeWorker(self):
        # worker + composite => CompositeConsumer
        worker = BaseWorker(Request.ANY, Offer())
        worker2 =BaseWorker(Request.ANY, Offer())
        worker3 =BaseWorker(Request.ANY, Offer())
        worker4 =BaseWorker(Request.ANY, Offer())
        result = (worker + worker2) + (worker3 + worker4)
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.consumers()), {worker})
        self.assertEqual(set(result.producers()), {worker4})
        self.assertEqual(set(result.internals()), {worker, worker2,
                                                   worker3, worker4})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(set(worker.observers()), {worker2})
        self.assertEqual(set(worker2.observed()), {worker})
        self.assertEqual(set(worker2.observers()), {worker3})
        self.assertEqual(set(worker3.observed()), {worker2})
        self.assertEqual(set(worker3.observers()), {worker4})
        self.assertEqual(set(worker4.observed()), {worker3})
        self.assertEqual(len(set(worker4.observers())), 1)

    def test__or__None(self):
        composite = BaseWorker(Request.ANY, Offer()) | \
            BaseWorker(Request.ANY, Offer())
        # composite | None = composite
        self.assertEqual(composite|None, composite)

    def test__ror__None(self):
        composite = BaseWorker(Request.ANY, Offer()) | \
            BaseWorker(Request.ANY, Offer())
        # None | composite = composite
        self.assertEqual(None|composite, composite)

    def test__or__Producer(self):
        # composite | prod => CompositeWorker
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        prod = Producer(Offer())
        result = (worker | worker2) | prod
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.producers()), {prod, worker, worker2})
        self.assertEqual(set(result.consumers()), {worker, worker2})
        self.assertEqual(set(result.internals()), {prod, worker, worker2})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(len(set(worker2.observed())), 1)
        self.assertEqual(len(set(prod.observers())), 1)
        self.assertEqual(len(set(worker.observers())), 1)
        self.assertEqual(len(set(worker2.observers())), 1)

    def test__or__Consumer(self):
        # composite | cons => CompositeWorker
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        cons = Consumer(Request.ANY)
        result = (worker | worker2) | cons
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.producers()), {worker, worker2})
        self.assertEqual(set(result.consumers()), {cons, worker, worker2})
        self.assertEqual(set(result.internals()), {cons, worker, worker2})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(len(set(worker2.observed())), 1)
        self.assertEqual(len(set(cons.observed())), 1)
        self.assertEqual(len(set(worker.observers())), 1)
        self.assertEqual(len(set(worker2.observers())), 1)

    def test__or__Worker(self):
        # composite | worker => CompositeWorker
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        worker3 = BaseWorker(Request.ANY, Offer())
        result = (worker | worker2) | worker3
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.producers()), {worker, worker2, worker3})
        self.assertEqual(set(result.consumers()), {worker, worker2, worker3})
        self.assertEqual(set(result.internals()), {worker, worker2, worker3})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(len(set(worker2.observed())), 1)
        self.assertEqual(len(set(worker3.observed())), 1)
        self.assertEqual(len(set(worker.observers())), 1)
        self.assertEqual(len(set(worker2.observers())), 1)
        self.assertEqual(len(set(worker3.observers())), 1)

    def test__or__CompositeProducer(self):
        # composite | composite => CompositeWorker
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        prod = Producer(Offer())
        prod2 = Producer(Offer())
        result = (worker | worker2) | (prod | prod2)
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.producers()), {prod, prod2, worker, worker2})
        self.assertEqual(set(result.consumers()), {worker, worker2})
        self.assertEqual(set(result.internals()), {prod, prod2, worker, worker2})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(len(set(worker2.observed())), 1)
        self.assertEqual(len(set(prod.observers())), 1)
        self.assertEqual(len(set(prod2.observers())), 1)
        self.assertEqual(len(set(worker.observers())), 1)
        self.assertEqual(len(set(worker2.observers())), 1)

    def test__or_CompositeConsumer(self):
        # composite | composite => CompositeWorker
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        cons = Consumer(Request.ANY)
        cons2 = Consumer(Request.ANY)
        result = (worker | worker2) | (cons | cons2)
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.producers()), {worker, worker2})
        self.assertEqual(set(result.consumers()), {cons, cons2, worker, worker2})
        self.assertEqual(set(result.internals()), {cons, cons2, worker, worker2})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(len(set(worker2.observed())), 1)
        self.assertEqual(len(set(cons.observed())), 1)
        self.assertEqual(len(set(cons2.observed())), 1)
        self.assertEqual(len(set(worker.observers())), 1)
        self.assertEqual(len(set(worker2.observers())), 1)

    def test__or__CompositeWorker(self):
        # composite | composite => CompositeWorker
        worker = BaseWorker(Request.ANY, Offer())
        worker2 = BaseWorker(Request.ANY, Offer())
        worker3 = BaseWorker(Request.ANY, Offer())
        worker4 = BaseWorker(Request.ANY, Offer())
        result = (worker | worker2) | (worker3 | worker4)
        self.assertIsInstance(result, CompositeWorker)
        self.assertEqual(set(result.producers()),
                         {worker, worker2, worker3, worker4})
        self.assertEqual(set(result.consumers()),
                         {worker, worker2, worker3, worker4})
        self.assertEqual(set(result.internals()),
                         {worker, worker2, worker3, worker4})
        self.assertEqual(len(set(worker.observed())), 1)
        self.assertEqual(len(set(worker2.observed())), 1)
        self.assertEqual(len(set(worker3.observed())), 1)
        self.assertEqual(len(set(worker4.observed())), 1)
        self.assertEqual(len(set(worker.observers())), 1)
        self.assertEqual(len(set(worker2.observers())), 1)
        self.assertEqual(len(set(worker3.observers())), 1)
        self.assertEqual(len(set(worker4.observers())), 1)

# -------------------------------------------------------------------

def suite():
    testcases = (
        TestRequest,
        TestLambdaRequest,
        Test_CompositeRequest,
        TestProducer,
        TestConsumer,
        TestConfigurableConsumer,
        TestBaseWorker,
        TestCompositeProducer,
        TestCompositeConsumer,
        TestCompositeWorker,
        )
    return unittest.TestSuite(itertools.chain(
            *(map(t, filter(lambda f: f.startswith("test_"), dir(t))) \
                  for t in testcases)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
