#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# unittest/eventloop/test_ProducerConsumer.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import unittest, weakref

from boing.eventloop.EventLoop import EventLoop
from boing.eventloop.ProducerConsumer import Producer, Consumer

class TestConsumer(Consumer):
    def __init__(self, hz=None):
        super().__init__(hz)
        self.store = {}

    def _consume(self, products, producer):
        l = self.store.setdefault(producer, [])
        l += products

def produce(tid, producer, product):
    producer._postProduct(product)

class TestProducerConsumer(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        EventLoop.stop()

    def test_add_remove_observers(self):
        p = Producer()
        c1 = Consumer()
        c2 = Consumer()
        ref_p = weakref.ref(p)
        ref_c1 = weakref.ref(c1)
        ref_c2 = weakref.ref(c2)
        self.assertFalse(p.addObserver(None))
        self.assertFalse(p.addObserver(12))
        self.assertFalse(p.addObserver("test"))
        self.assertTrue(p.addObserver(c1))
        self.assertFalse(p.addObserver(c1))
        self.assertEqual(p.observers(), {c1})
        self.assertTrue(p.addObserver(c2))
        self.assertFalse(p.addObserver(c2))
        self.assertEqual(p.observers(), {c1, c2})
        self.assertTrue(p.removeObserver(c1))
        self.assertFalse(p.removeObserver(c1))
        del c1
        self.assertIsNone(ref_c1())
        self.assertEqual(p.observers(), {c2})
        self.assertTrue(p.removeObserver(c2))
        self.assertFalse(p.removeObserver(c2))
        del c2
        self.assertIsNone(ref_c2())
        self.assertIsInstance(p.observers(), frozenset)
        self.assertFalse(p.observers())
        del p
        self.assertIsNone(ref_p())

    def test_add_delete_observers(self):
        p = Producer()
        c1 = Consumer()
        c2 = Consumer()
        ref_p = weakref.ref(p)
        ref_c1 = weakref.ref(c1)
        ref_c2 = weakref.ref(c2)
        p.addObserver(c1)
        self.assertEqual(p.observers(), {c1})
        p.addObserver(c2)
        self.assertEqual(p.observers(), {c1, c2})
        del c1
        self.assertIsNone(ref_c1())
        self.assertEqual(p.observers(), {c2})
        del c2
        self.assertIsNone(ref_c2())
        self.assertIsInstance(p.observers(), frozenset)
        self.assertFalse(p.observers())
        del p
        self.assertIsNone(ref_p())

    def test_production_1(self):
        # init objects
        p1 = Producer()
        p2 = Producer()
        c1 = TestConsumer()
        c1.subscribeTo(p1)
        c1.subscribeTo(p2)
        c2 = TestConsumer(None)
        c2.subscribeTo(p1)
        c2.subscribeTo(p2)
        c3 = TestConsumer(3)
        c3.subscribeTo(p1)
        c3.subscribeTo(p2)
        # test observation
        statue = "statue"
        temple = "temple"
        EventLoop.after(.2, produce, p1, statue)
        EventLoop.after(.25, produce, p1, statue)        
        EventLoop.after(.25, produce, p2, temple)
        EventLoop.after(.45, produce, p1, temple)
        EventLoop.after(.45, produce, p2, statue)        
        EventLoop.runFor(.5)
        # Check results
        self.assertEqual(c1.store[p1], [statue, statue, temple])
        self.assertEqual(c1.store[p2], [temple, statue])
        self.assertEqual(c2.store[p1], [statue, statue, temple])
        self.assertEqual(c2.store[p2], [temple, statue])
        self.assertEqual(c3.store[p1], [statue, statue])
        self.assertEqual(c3.store[p2], [temple])        
        # Clean results
        c1.store = None
        c2.store = None
        c3.store = None
        # test p1 deletion
        ref = weakref.ref(p1)
        del p1
        self.assertIsNone(ref())
        # test p2 deletion
        ref = weakref.ref(p2)
        del p2
        self.assertIsNone(ref())
        # test c1 deletion
        ref = weakref.ref(c1)
        del c1
        self.assertIsNone(ref())
        # test c2 deletion
        ref = weakref.ref(c2)
        del c2
        self.assertIsNone(ref())
        # test c3 deletion
        ref = weakref.ref(c3)
        del c3
        self.assertIsNone(ref())

# -------------------------------------------------------------------

def suite():    
    tests = list(t for t in TestProducerConsumer.__dict__ \
                   if t.startswith("test_"))
    return unittest.TestSuite(map(TestProducerConsumer, tests))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
