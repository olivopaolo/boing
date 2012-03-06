#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# unittest/eventloop/test_ReactiveObject.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import itertools
import sys
import unittest
import weakref

from PyQt4 import QtCore

from boing.eventloop.ReactiveObject import Observable, ReactiveObject, \
                                           DelayedReactive

class TestReactiveObject(ReactiveObject):
    def __init__(self):
        ReactiveObject.__init__(self)
        self.reaction = 0

    def _react(self):
        self.reaction += 1


class TestDelayedReactive(DelayedReactive):
    def __init__(self, hz=None):
        DelayedReactive.__init__(self, hz)
        self.refresh = 0

    def _refresh(self):
        self.refresh += 1

# -------------------------------------------------------------------

class testReactiveObject(unittest.TestCase):

    def setUp(self):
        self.app = QtCore.QCoreApplication(sys.argv)

    def tearDown(self):
        self.app.exit()
        self.app = None

    def test_observer_creation(self):
        o = Observable()
        ref = weakref.ref(o)
        self.assertFalse(tuple(o.observers()))
        o.notifyObservers()
        del o
        self.assertIsNone(ref())
        
    def test_reactive_creation(self):
        r = ReactiveObject()
        ref = weakref.ref(r)
        self.assertFalse(tuple(r.observed()))
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
        self.assertEqual(set(o.observers()), {r1})
        self.assertTrue(o.addObserver(r2))
        self.assertFalse(o.addObserver(r2))
        self.assertEqual(set(o.observers()), {r1, r2})
        self.assertTrue(o.removeObserver(r1))
        self.assertFalse(o.removeObserver(r1))
        self.assertEqual(set(o.observers()), {r2})
        self.assertTrue(o.removeObserver(r2))
        self.assertFalse(o.removeObserver(r2))
        self.assertFalse(set(o.observers()))

    def test_add_delete_observers(self):
        o = Observable()
        r1 = ReactiveObject()
        r2 = ReactiveObject()
        ref_o = weakref.ref(o)
        ref_r1 = weakref.ref(r1)
        ref_r2 = weakref.ref(r2)
        o.addObserver(r1)
        self.assertEqual(set(o.observers()), {r1})
        o.addObserver(r2)
        self.assertEqual(set(o.observers()), {r1, r2})
        del r1
        self.assertIsNone(ref_r1())
        self.assertEqual(set(o.observers()), {r2})
        del r2
        self.assertIsNone(ref_r2())
        self.assertFalse(set(o.observers()))
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
        self.assertEqual(set(r.observed()), {o1})
        self.assertTrue(r.subscribeTo(o2))
        self.assertFalse(r.subscribeTo(o2))
        self.assertEqual(set(r.observed()), {o1, o2})
        self.assertTrue(r.unsubscribeFrom(o1))
        self.assertFalse(r.unsubscribeFrom(o1))
        self.assertEqual(set(r.observed()), {o2})
        self.assertTrue(r.unsubscribeFrom(o2))
        self.assertFalse(r.unsubscribeFrom(o2))
        self.assertFalse(set(r.observed()))

    def test_subscribe_delete(self):
        o1 = Observable()
        o2 = Observable()
        r = ReactiveObject()
        ref_o1 = weakref.ref(o1)
        ref_o2 = weakref.ref(o2)
        ref_r = weakref.ref(r)
        r.subscribeTo(o1)
        self.assertEqual(set(r.observed()), {o1})
        r.subscribeTo(o2)
        self.assertEqual(set(r.observed()), {o1, o2})
        del o1
        self.assertIsNone(ref_o1())
        self.assertEqual(set(r.observed()), {o2})
        del o2
        self.assertIsNone(ref_o2())
        self.assertFalse(set(r.observed()))
        del r
        self.assertIsNone(ref_r())

    def test_clearObservable(self):
        o = Observable()
        o.clearObservers()
        r1 = ReactiveObject()        
        r2 = ReactiveObject()
        r1.subscribeTo(o)
        r2.subscribeTo(o)
        o.clearObservers()
        self.assertFalse(set(o.observers()))
    
    def test_trigger(self):
        obs = []
        for period in (100,150,200):
            o = Observable()
            tid = QtCore.QTimer(o)
            tid.timeout.connect(o.notifyObservers)
            tid.start(period)
            obs.append(o)
        obsrefs = [weakref.ref(o) for o in obs]
        reacts = [TestReactiveObject() for i in range(2)]
        reactsrefs = [weakref.ref(r) for r in reacts]
        for o, r in itertools.product(obs, reacts): 
            r.subscribeTo(o)
        del o, r
        setter = lambda obj, key, value: obj.__setitem__(key, value)
        QtCore.QTimer.singleShot(400, lambda : setter(obs, 2, None))
        QtCore.QTimer.singleShot(500, lambda : setter(reacts, 1, None))
        QtCore.QTimer.singleShot(600, self.app.quit)
        self.app.exec_()
        self.assertEqual(set(obs[0].observers()), set(reacts[:1]))
        self.assertEqual(set(obs[1].observers()), set(reacts[:1]))
        self.assertEqual(set(reacts[0].observed()), set(obs[:2]))
        self.assertGreater(reacts[0].reaction, 0)
        del obs, reacts
        for ref in itertools.chain(obsrefs, reactsrefs):            
            self.assertIsNone(ref())

class test_DelayedReactive(unittest.TestCase):

    def setUp(self):
        self.app = QtCore.QCoreApplication(sys.argv)

    def tearDown(self):
        self.app.exit()
        self.app = None

    def test_creation_empty(self):
        r = DelayedReactive()
        self.assertFalse(set(r.observed()))
        self.assertFalse(set(r.queue()))
        ref = weakref.ref(r)
        del r
        self.assertIsNone(ref())

    def test_creation_None(self):
        r = DelayedReactive(None)
        self.assertFalse(set(r.observed()))
        self.assertFalse(set(r.queue()))
        ref = weakref.ref(r)
        del r
        self.assertIsNone(ref())

    def test_creation_value(self):
        r = DelayedReactive()
        self.assertFalse(set(r.observed()))
        self.assertFalse(set(r.queue()))
        ref = weakref.ref(r)
        del r
        self.assertIsNone(ref())

    def test_add_remove_observers(self):
        o = Observable()
        r1 = DelayedReactive()
        r2 = DelayedReactive()
        o.addObserver(r1)
        self.assertEqual(set(o.observers()), {r1})
        o.addObserver(r2)
        self.assertEqual(set(o.observers()), {r1, r2})
        o.removeObserver(r1)
        self.assertEqual(set(o.observers()), {r2})
        o.removeObserver(r2)
        self.assertFalse(set(o.observers()))

    def test_add_delete_observers(self):
        o = Observable()
        r1 = DelayedReactive()
        r2 = DelayedReactive()
        ref_o = weakref.ref(o)
        ref_r1 = weakref.ref(r1)
        ref_r2 = weakref.ref(r2)
        o.addObserver(r1)
        self.assertEqual(set(o.observers()), {r1})
        o.addObserver(r2)
        self.assertEqual(set(o.observers()), {r1, r2})
        del r1
        self.assertIsNone(ref_r1())
        self.assertEqual(set(o.observers()), {r2})
        del r2
        self.assertIsNone(ref_r2())
        self.assertFalse(set(o.observers()))
        del o
        self.assertIsNone(ref_o())

    def test_clearObserved(self):
        r = ReactiveObject()        
        r.clearObserved()
        o1 = Observable()
        o2 = Observable()
        r.subscribeTo(o1)
        r.subscribeTo(o2)
        r.clearObserved()
        self.assertFalse(set(r.observed()))

    def test_trigger(self):
        obs = []
        for period in (100,150,200):
            o = Observable()
            tid = QtCore.QTimer(o)
            tid.timeout.connect(o.notifyObservers)
            tid.start(period)
            obs.append(o)
        obsrefs = [weakref.ref(o) for o in obs]
        reacts = [TestDelayedReactive(hz) for hz in (None, 9, None, 9)]
        reactsrefs = [weakref.ref(r) for r in reacts]
        for o, r in itertools.product(obs, reacts): 
            r.subscribeTo(o)
        del o, r
        setter = lambda obj, key, value: obj.__setitem__(key, value)
        QtCore.QTimer.singleShot(300, lambda : setter(obs, 2, None))
        QtCore.QTimer.singleShot(400, lambda : setter(reacts, 2, None))
        QtCore.QTimer.singleShot(500, lambda : setter(reacts, 3, None))
        QtCore.QTimer.singleShot(600, self.app.quit)
        self.app.exec_()
        self.assertEqual(set(obs[0].observers()), set(reacts[:2]))
        self.assertEqual(set(obs[1].observers()), set(reacts[:2]))
        self.assertEqual(set(reacts[0].observed()), set(obs[:2]))
        self.assertEqual(set(reacts[1].observed()), set(obs[:2]))
        self.assertGreater(reacts[0].refresh, 0)
        self.assertGreater(reacts[1].refresh, 0)
        del obs, reacts
        for ref in itertools.chain(obsrefs, reactsrefs):            
            self.assertIsNone(ref())

# -------------------------------------------------------------------

def suite():    
    reactiveobject_tests = (t for t in testReactiveObject.__dict__ \
                                  if t.startswith("test_"))
    delayedreactive_tests = (t for t in test_DelayedReactive.__dict__ \
                                   if t.startswith("test_"))
    return unittest.TestSuite(itertools.chain(
            map(testReactiveObject, reactiveobject_tests),
            map(test_DelayedReactive, delayedreactive_tests)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
