#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# boing/test/core/test_observer.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import itertools
import unittest
import weakref

from PyQt4 import QtCore

from boing.core.observer import StandardObservable, SelectiveObservable, Observer
from boing.test import QtBasedTest

def testReact(observer, observable):
    observer.hit = 0 if not hasattr(observer, "hit") else observer.hit + 1

class TestConcreteObservable(QtBasedTest):

    def test_creation(self):
        obs = self.classobj()  
        ref = weakref.ref(obs)
        del obs
        self.assertIsNone(ref())
        
    def test_addObservers(self):
        observable = self.classobj()
        ref = weakref.ref(observable)
        self.assertRaises(TypeError, observable.addObserver, None)
        self.assertRaises(TypeError, observable.addObserver, "wrong")
        self.assertRaises(TypeError, observable.addObserver, self.classobj())
        obs1 = Observer()
        ref1 = weakref.ref(obs1)
        self.assertTrue(observable.addObserver(obs1))
        self.assertFalse(observable.addObserver(obs1))
        obs2 = Observer()
        self.assertTrue(observable.addObserver(obs2))
        del obs1
        self.assertIsNone(ref1())
        del observable
        self.assertIsNone(ref())
    
    def test_removeObserver(self):
        observable = self.classobj()
        self.assertFalse(observable.removeObserver(None))
        self.assertFalse(observable.removeObserver("wrong"))
        self.assertFalse(observable.removeObserver(self.classobj()))
        obs1 = Observer()
        observable.addObserver(obs1)
        obs2 = Observer()
        observable.addObserver(obs2)
        self.assertTrue(observable.removeObserver(obs1))
        self.assertFalse(observable.removeObserver(obs1))
        self.assertTrue(observable.removeObserver(obs2))
        
    def test_observers(self):
        observable = self.classobj()
        self.assertEqual(set(observable.observers()), set())
        obs1 = Observer()
        observable.addObserver(obs1)
        self.assertEqual(set(observable.observers()), {obs1})
        obs2 = Observer()
        observable.addObserver(obs2)
        self.assertEqual(set(observable.observers()), {obs1, obs2})
        del obs1
        self.assertEqual(set(observable.observers()), {obs2})
        del obs2
        self.assertEqual(set(observable.observers()), set())

    def test_clear(self):
        observable = self.classobj()
        observable.clear()
        obs1 = Observer()
        observable.addObserver(obs1)
        obs2 = Observer()
        observable.addObserver(obs2)
        observable.clear()
        self.assertEqual(set(observable.observers()), set())

    def trigger_test(self, mode):        
        # Init observables
        observables = []
        for i, period in enumerate((100,150,200)):
            observables.append(StandardObservable())
            tid = QtCore.QTimer(observables[i], timeout=observables[i].notify)
            tid.start(period)
        del i, period
        # Init observers
        observers = []
        for hz in (None, None, 0, 1, 60, 60000, "inf"):
            observers.append(Observer(react=testReact, hz=hz))
        # Subscriptions
        for observable, observer in itertools.product(observables, observers): 
            observer.subscribeTo(observable, mode)
            del observable, observer
        # Delete instances during eventloop
        setter = lambda obj, key, value: obj.__setitem__(key, value)
        QtCore.QTimer.singleShot(400, lambda : setter(observables, 0, None))
        QtCore.QTimer.singleShot(500, lambda : setter(observers, 0, None))
        QtCore.QTimer.singleShot(600, self.app.quit)
        # Exec
        self.app.exec_()
        # Check element deletion
        for obs in filter(None, observables):
            self.assertEqual(set(obs.observers()), set(observers[1:]))
        for obs in filter(None, observers):
            self.assertEqual(set(obs.observed()), set(observables[1:]))
        # Check react func
        self.assertGreater(observers[1].hit, 0)
        self.assertFalse(hasattr(observers[2], "hit"))
        self.assertFalse(hasattr(observers[3], "hit"))
        self.assertGreater(observers[4].hit, 0)
        self.assertGreater(observers[5].hit, 0)
        self.assertGreater(observers[6].hit, 0)

    def test_trigger_direct(self):
        self.trigger_test(QtCore.Qt.DirectConnection)

    def test_trigger_queued(self):
        self.trigger_test(QtCore.Qt.QueuedConnection)

    
class TestStandardObservable(TestConcreteObservable):

    def setUp(self):
        super().setUp()
        self.classobj = StandardObservable


class TestSelectiveObservable(TestConcreteObservable):

    def setUp(self):
        super().setUp()
        self.classobj = SelectiveObservable

    def test_addObservers(self):
        super().test_addObservers()
        observable = SelectiveObservable()
        ref = weakref.ref(observable)
        obs1 = Observer()
        ref1 = weakref.ref(obs1)
        self.assertTrue(observable.addObserver(obs1))
        self.assertFalse(observable.addObserver(obs1))
        obs2 = Observer()
        self.assertTrue(observable.addObserver(obs2))
        del obs1
        self.assertIsNone(ref1())
        del observable
        self.assertIsNone(ref())

    def trigger_observer_test(self, mode):
        # Values are set to that:
        #
        # - the first observer is deleted during eventloop;
        #
        # - observers[1:5] won't be triggered because of hz value(0
        #    and 1);
        #
        # - observers[5::2] will be triggered because selection is True;
        #
        # - observers[6::2] will not be triggered because selection is
        #   False (i.e. observer not in *args at obs.notify(*args));
        hzs = (None, 0, 0, 1, 1, None, None, 60, 60, 60000, 60000, "inf", "inf")
        selection =  (0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0)
        # Init observers
        observers = []
        for hz in hzs:
            observers.append(Observer(react=testReact, hz=hz))
        # Init observables
        observables = []
        def trigger(obs):
            obs.notify(*list(itertools.compress(observers, selection)))
        for i, period in enumerate((100,150,200)):
            observables.append(SelectiveObservable())
            tid = QtCore.QTimer(parent=observables[i], 
                                timeout=lambda : trigger(observables[i]))
            tid.start(period)
        # Subscriptions
        for observer, observable in itertools.product(observers, observables):
            self.assertTrue(observable.addObserver(observer, mode))
        del observable, observer
        # Delete instances during eventloop
        setter = lambda obj, key, value: obj.__setitem__(key, value)
        QtCore.QTimer.singleShot(400, lambda : setter(observables, 0, None))
        QtCore.QTimer.singleShot(500, lambda : setter(observers, 0, None))
        QtCore.QTimer.singleShot(600, self.app.quit)
        # Exec
        self.app.exec_()
        # Check element deletion
        for obs in filter(None, observables):
            self.assertEqual(set(obs.observers()), set(observers[1:]))
        for obs in filter(None, observers):
            self.assertEqual(set(obs.observed()), set(observables[1:]))
        # Check react func
        for i in range(5, 13, 2):
            self.assertGreater(observers[i].hit, 0)
            self.assertFalse(hasattr(observers[i+1], "hit"))

    def test_trigger_observer_direct(self):
        self.trigger_observer_test(QtCore.Qt.DirectConnection)

    def test_trigger_observer_queued(self):
        self.trigger_observer_test(QtCore.Qt.QueuedConnection)


class TestObserver(QtBasedTest):

    concreteObservables = (StandardObservable, 
                           SelectiveObservable)

    def test_creation_empty(self):
        obs = Observer()
        ref = weakref.ref(obs)
        del obs
        self.assertIsNone(ref())

    def test_creation_None(self):
        obs = Observer(hz=None)
        self.assertIsNone(obs.hz())
        ref = weakref.ref(obs)
        del obs
        self.assertIsNone(ref())

    def test_creation_hz(self):
        obs = Observer(hz=60)
        self.assertEqual(obs.hz(), 60)
        ref = weakref.ref(obs)
        del obs
        self.assertIsNone(ref())

    def test_creation_inf(self):
        obs = Observer(hz="inf")
        self.assertEqual(obs.hz(), float("inf"))
        ref = weakref.ref(obs)
        del obs
        self.assertIsNone(ref())

    def test_creation_react_func(self):
        obs = Observer(testReact)

    def test_creation_react_None(self):
        obs = Observer(None)

    def test_creation_react_raises(self):
        self.assertRaises(TypeError, Observer, 1)
        self.assertRaises(TypeError, Observer, "asd")
        self.assertRaises(TypeError, Observer, object())

    def test_subscribeTo(self):
        obs = Observer()
        self.assertRaises(TypeError, obs.subscribeTo, None)
        self.assertRaises(TypeError, obs.subscribeTo, "wrong")
        self.assertRaises(TypeError, obs.subscribeTo, Observer())
        del obs
        for obsclass in TestObserver.concreteObservables:
            observer = Observer()
            ref = weakref.ref(observer)
            obs1 = obsclass()
            ref1 = weakref.ref(obs1)
            self.assertTrue(observer.subscribeTo(obs1))
            self.assertFalse(observer.subscribeTo(obs1))
            obs2 = obsclass()
            self.assertTrue(observer.subscribeTo(obs2))
            del obs1
            self.assertIsNone(ref1())
            del observer
            self.assertIsNone(ref())

    def test_unsubscribeFrom(self):
        observer = Observer()
        self.assertFalse(observer.unsubscribeFrom(None))
        self.assertFalse(observer.unsubscribeFrom("wrong"))
        self.assertFalse(observer.unsubscribeFrom(Observer()))
        for obsclass in TestObserver.concreteObservables:
            obs1 = obsclass()
            observer.subscribeTo(obs1)
            obs2 = obsclass()
            observer.subscribeTo(obs2)
            self.assertTrue(observer.unsubscribeFrom(obs1))
            self.assertFalse(observer.unsubscribeFrom(obs1))
            self.assertTrue(observer.unsubscribeFrom(obs2))

    def test_observed(self):
        observer = Observer()
        self.assertEqual(set(observer.observed()), set())
        for obsclass in TestObserver.concreteObservables:
            obs1 = obsclass()
            observer.subscribeTo(obs1)
            self.assertEqual(set(observer.observed()), {obs1})
            obs2 = obsclass()
            observer.subscribeTo(obs2)
            self.assertEqual(set(observer.observed()), {obs1, obs2})
            del obs1
            self.assertEqual(set(observer.observed()), {obs2})
            del obs2
            self.assertEqual(set(observer.observed()), set())

    def test_clear(self):
        observer = Observer()
        observer.clear()
        for obsclass in TestObserver.concreteObservables:
            obs1 = obsclass()
            observer.subscribeTo(obs1)
            obs2 = obsclass()
            observer.subscribeTo(obs2)
            observer.clear()
            self.assertEqual(set(observer.observed()), set())

# -------------------------------------------------------------------

def suite():    
    testcases = (
        TestStandardObservable,
        TestSelectiveObservable,
        TestObserver,
        )
    return unittest.TestSuite(itertools.chain(
            *(map(t, filter(lambda f: f.startswith("test_"), dir(t))) \
                  for t in testcases)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
