#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# unittest/eventloop/test_ReactiveObject.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import unittest
import weakref

from boing.eventloop.EventLoop import EventLoop
from boing.eventloop.ReactiveObject import Observable, ReactiveObject, \
                                           DelayedReactive

def notify(tid, obs, *args, **kwargs):
    obs.notifyObservers()

class TestReactiveObject(ReactiveObject):
    def __init__(self):
        super().__init__()
        self.reaction = 0

    def _react(self):
        self.reaction += 1


class TestDelayedReactive(DelayedReactive):
    def __init__(self, hz=None):
        super().__init__(hz)
        self.refresh = 0

    def _refresh(self):
        self.refresh += 1

# -------------------------------------------------------------------

class testReactiveObject(unittest.TestCase):

    def test_observer_creation(self):
        o = Observable()
        ref = weakref.ref(o)
        self.assertIsInstance(o.observers(), frozenset)
        self.assertFalse(o.observers())
        o.notifyObservers()
        del o
        self.assertIsNone(ref())
        
    def test_reactive_creation(self):
        r = ReactiveObject()
        ref = weakref.ref(r)
        self.assertIsInstance(r.observed(), frozenset)
        self.assertFalse(r.observed())
        del r
        self.assertIsNone(ref())

    def test_add_remove_observers(self):
        o = Observable()
        self.assertFalse(o.addObserver(None))
        self.assertFalse(o.addObserver(12))
        self.assertFalse(o.addObserver("test"))
        r1 = ReactiveObject()
        r2 = ReactiveObject()
        self.assertTrue(o.addObserver(r1))
        self.assertFalse(o.addObserver(r1))
        self.assertEqual(o.observers(), {r1})
        self.assertTrue(o.addObserver(r2))
        self.assertFalse(o.addObserver(r2))
        self.assertEqual(o.observers(), {r1, r2})
        self.assertTrue(o.removeObserver(r1))
        self.assertFalse(o.removeObserver(r1))
        self.assertEqual(o.observers(), {r2})
        self.assertTrue(o.removeObserver(r2))
        self.assertFalse(o.removeObserver(r2))
        self.assertIsInstance(o.observers(), frozenset)
        self.assertFalse(o.observers())

    def test_add_delete_observers(self):
        o = Observable()
        r1 = ReactiveObject()
        r2 = ReactiveObject()
        ref_o = weakref.ref(o)
        ref_r1 = weakref.ref(r1)
        ref_r2 = weakref.ref(r2)
        o.addObserver(r1)
        self.assertEqual(o.observers(), {r1})
        o.addObserver(r2)
        self.assertEqual(o.observers(), {r1, r2})
        del r1
        self.assertIsNone(ref_r1())
        self.assertEqual(o.observers(), {r2})
        del r2
        self.assertIsNone(ref_r2())
        self.assertIsInstance(o.observers(), frozenset)
        self.assertFalse(o.observers())
        del o
        self.assertIsNone(ref_o())

    def test_subscribe_unsubscribe(self):
        o1 = Observable()
        o2 = Observable()
        r = ReactiveObject()
        self.assertFalse(r.subscribeTo(None))
        self.assertFalse(r.subscribeTo(21))
        self.assertFalse(r.subscribeTo("test"))
        self.assertTrue(r.subscribeTo(o1))
        self.assertFalse(r.subscribeTo(o1))
        self.assertEqual(r.observed(), {o1})
        self.assertTrue(r.subscribeTo(o2))
        self.assertFalse(r.subscribeTo(o2))
        self.assertEqual(r.observed(), {o1, o2})
        self.assertTrue(r.unsubscribeFrom(o1))
        self.assertFalse(r.unsubscribeFrom(o1))
        self.assertEqual(r.observed(), {o2})
        self.assertTrue(r.unsubscribeFrom(o2))
        self.assertFalse(r.unsubscribeFrom(o2))
        self.assertIsInstance(r.observed(), frozenset)
        self.assertFalse(r.observed())

    def test_subscribe_delete(self):
        o1 = Observable()
        o2 = Observable()
        r = ReactiveObject()
        ref_o1 = weakref.ref(o1)
        ref_o2 = weakref.ref(o2)
        ref_r = weakref.ref(r)
        r.subscribeTo(o1)
        self.assertEqual(r.observed(), {o1})
        r.subscribeTo(o2)
        self.assertEqual(r.observed(), {o1, o2})
        del o1
        self.assertIsNone(ref_o1())
        self.assertEqual(r.observed(), {o2})
        del o2
        self.assertIsNone(ref_o2())
        self.assertIsInstance(r.observed(), frozenset)
        self.assertFalse(r.observed())
        del r
        self.assertIsNone(ref_r())
    
    def test_trigger(self):
        def del_reactiveobject(tid, target, test_instance, *args, **kwargs):
            test_instance.assertGreater(target.reaction, 0)
            del target
        def del_observable(tid, target, timer, *args, **kwargs):
            EventLoop.cancel_timer(timer)
            del target
        # Init objects
        o1 = Observable()
        o2 = Observable()
        o3 = Observable()
        ref_o1 = weakref.ref(o1)
        ref_o2 = weakref.ref(o2)
        ref_o3 = weakref.ref(o3)
        r1 = TestReactiveObject()
        r2 = TestReactiveObject()
        ref_r1 = weakref.ref(r1)
        ref_r2 = weakref.ref(r2)
        o1.addObserver(r1)
        o1.addObserver(r2)
        o2.addObserver(r1)
        o2.addObserver(r2)
        o3.addObserver(r1)
        o3.addObserver(r2)
        # test observation
        t_o1 = EventLoop.repeat_every(.1, notify, o1)
        t_o2 = EventLoop.repeat_every(.2, notify, o2)        
        t_o3 = EventLoop.repeat_every(.15, notify, o3)
        t_del_r2 = EventLoop.after(.4, del_reactiveobject, r2, self)
        t_del_o3 = EventLoop.after(.5, del_observable, o3, t_o3)
        del r2, o3
        EventLoop.runFor(.6)
        EventLoop.cancel_timer(t_o1)
        EventLoop.cancel_timer(t_o2)
        EventLoop.cancel_timer(t_del_o3)
        EventLoop.cancel_timer(t_del_r2)
        self.assertEqual(o1.observers(), {r1})
        self.assertEqual(o2.observers(), {r1})
        self.assertEqual(r1.observed(), {o1, o2})
        self.assertGreater(r1.reaction, 0)
        del o1, o2, r1
        self.assertIsNone(ref_o1())
        self.assertIsNone(ref_o2())
        self.assertIsNone(ref_o3())
        self.assertIsNone(ref_r1())
        self.assertIsNone(ref_r2())


class test_DelayedReactive(unittest.TestCase):

    def test_creation_empty(self):
        r = DelayedReactive()
        self.assertIsInstance(r.observed(), frozenset)
        self.assertIsInstance(r.queue(), frozenset)
        self.assertFalse(r.observed())
        self.assertFalse(r.queue())
        ref = weakref.ref(r)
        del r
        self.assertIsNone(ref())

    def test_creation_None(self):
        r = DelayedReactive(None)
        self.assertIsInstance(r.observed(), frozenset)
        self.assertIsInstance(r.queue(), frozenset)
        self.assertFalse(r.observed())
        self.assertFalse(r.queue())
        ref = weakref.ref(r)
        del r
        self.assertIsNone(ref())

    def test_creation_value(self):
        r = DelayedReactive()
        self.assertIsInstance(r.observed(), frozenset)
        self.assertIsInstance(r.queue(), frozenset)
        self.assertFalse(r.observed())
        self.assertFalse(r.queue())
        ref = weakref.ref(r)
        del r
        self.assertIsNone(ref())

    def test_add_remove_observers(self):
        o = Observable()
        r1 = DelayedReactive()
        r2 = DelayedReactive()
        o.addObserver(r1)
        self.assertEqual(o.observers(), {r1})
        o.addObserver(r2)
        self.assertEqual(o.observers(), {r1, r2})
        o.removeObserver(r1)
        self.assertEqual(o.observers(), {r2})
        o.removeObserver(r2)
        self.assertIsInstance(o.observers(), frozenset)
        self.assertFalse(o.observers())

    def test_add_delete_observers(self):
        o = Observable()
        r1 = DelayedReactive()
        r2 = DelayedReactive()
        ref_o = weakref.ref(o)
        ref_r1 = weakref.ref(r1)
        ref_r2 = weakref.ref(r2)
        o.addObserver(r1)
        self.assertEqual(o.observers(), {r1})
        o.addObserver(r2)
        self.assertEqual(o.observers(), {r1, r2})
        del r1
        self.assertIsNone(ref_r1())
        self.assertEqual(o.observers(), {r2})
        del r2
        self.assertIsNone(ref_r2())
        self.assertIsInstance(o.observers(), frozenset)
        self.assertFalse(o.observers())
        del o
        self.assertIsNone(ref_o())

    def test_trigger(self):
        def del_reactiveobject(tid, target, test_instance, *args, **kwargs):
            test_instance.assertGreater(target.refresh, 0)
            del target
        def del_observable(tid, target, timer, *args, **kwargs):
            EventLoop.cancel_timer(timer)
            del target
        # Init objects
        o1 = Observable()
        o2 = Observable()
        ref_o1 = weakref.ref(o1)
        ref_o2 = weakref.ref(o2)
        r1 = TestDelayedReactive(None)
        r2 = TestDelayedReactive(8)
        r3 = TestDelayedReactive(None)
        r4 = TestDelayedReactive(8)
        ref_r1 = weakref.ref(r1)
        ref_r2 = weakref.ref(r2)
        ref_r3 = weakref.ref(r3)
        ref_r4 = weakref.ref(r4)
        o1.addObserver(r1)
        o1.addObserver(r2)
        o1.addObserver(r3)
        o1.addObserver(r4)
        o2.addObserver(r1)
        o2.addObserver(r2)
        o2.addObserver(r3)
        o2.addObserver(r4)
        # test observation
        t_o1 = EventLoop.repeat_every(.1, notify, o1)
        t_o2 = EventLoop.repeat_every(.2, notify, o2)        
        t_del_o2 = EventLoop.after(.3, del_observable, o2, t_o2)
        t_del_r2 = EventLoop.after(.4, del_reactiveobject, r2, self)
        t_del_r3 = EventLoop.after(.5, del_reactiveobject, r3, self)
        del o2, r2, r3
        EventLoop.runFor(.6)
        EventLoop.cancel_timer(t_o1)
        EventLoop.cancel_timer(t_o2)
        EventLoop.cancel_timer(t_del_o2)
        EventLoop.cancel_timer(t_del_r2)
        EventLoop.cancel_timer(t_del_r3)
        self.assertEqual(o1.observers(), {r1, r4})
        self.assertEqual(r1.observed(), {o1})
        self.assertEqual(r4.observed(), {o1})
        self.assertGreater(r1.refresh, 0)
        self.assertGreater(r4.refresh, 0)
        del o1, r1, r4
        self.assertIsNone(ref_o1())
        self.assertIsNone(ref_o2())
        self.assertIsNone(ref_r1())
        self.assertIsNone(ref_r2())
        self.assertIsNone(ref_r3())
        self.assertIsNone(ref_r4())

# -------------------------------------------------------------------

def suite():    
    reactiveobject_tests = list(t for t in testReactiveObject.__dict__ \
                                  if t.startswith("test_"))
    delayedreactive_tests = list(t for t in test_DelayedReactive.__dict__ \
                                   if t.startswith("test_"))
    return unittest.TestSuite(list(map(testReactiveObject, 
                                       reactiveobject_tests))+
                              list(map(test_DelayedReactive, 
                                       delayedreactive_tests)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
