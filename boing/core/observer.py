# -*- coding: utf-8 -*-
#
# boing/core/observer.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

"""
This module contains classes implementing the Observer design pattern.
"""

import collections
import sip
import sys
import weakref

from PyQt4 import QtCore

from boing.core.graph import Node
from boing.utils import assertIsInstance

class Observable(QtCore.QObject, Node):

    # FIXME: Add unittest for these signals
    observerAdded = QtCore.pyqtSignal(QtCore.QObject)
    observerRemoved = QtCore.pyqtSignal(QtCore.QObject)

    class _ObserverRecord(QtCore.QObject):

        trigger = QtCore.pyqtSignal(QtCore.QObject)

        def __init__(self, observer, mode):
            super().__init__()
            self.trigger.connect(observer._reactSlot, mode)


    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent)
        Node.__init__(self)
        self.__observers = dict()

    def __del__(self):
        if not sip.isdeleted(self):
            generator = ((ref(), record) for (ref, record) \
                             in self.__observers.items() if ref() is not None)
            for obs, record in generator:
                # Notify the subscribed observers they have a None reference.
                record.trigger.disconnect(obs._reactSlot)
                obs._checkRefs()
            # To make sure that the children's '__del__' method is invoked.
            for child in tuple(self.children()):
                child.setParent(None)
        Node.__del__(self)

    def observers(self):
        """Return an iterator over the subscribed observers."""
        return (ref() for ref in self.__observers.keys())

    def addObserver(self, observer, mode=QtCore.Qt.QueuedConnection, child=False):
        """Subscribe a new *observer*; return true if *observer* has been
        correctly added, false otherwise."""
        assertIsInstance(observer, Observer)
        if observer in self.observers(): 
            rvalue = False
        else:
            observer._addObservable(self)
            self.__observers[weakref.ref(observer)] = \
                Observable._ObserverRecord(observer, mode)
            if child: observer.setParent(self)
            self.observerAdded.emit(observer)
            rvalue = True
        return rvalue

    def removeObserver(self, observer):
        """Unsubscribe *observer*; return true if *observer* has been
        correcty found and removed, false otherwise."""
        ref = self._getRef(observer)
        if ref is None: rvalue = False
        else:
            record = self.__observers.pop(ref)
            record.trigger.disconnect(observer._reactSlot)
            observer._removeObservable(self)
            self.observerRemoved.emit(observer)
            rvalue = True
        return rvalue

    def clear(self):
        """Unsubscribe all registered observers."""
        for observer in tuple(self.observers()):
            self.removeObserver(observer)

    def notify(self, *restrictions):
        """Activate the trigger."""
        records = self.__observers.values() if not restrictions \
            else (record for ref, record in self.__observers.items() \
                      if ref() in restrictions)
        self._notifyFromRecords(records)

    def _notifyFromRecords(self, records):
        """Notify the observers associated to *records*."""
        for record in records:
            self._notifyRecord(record)

    def _notifyRecord(self, record):
        """Notify the observers associated to *record*."""
        record.trigger.emit(self)
            
    def _checkRefs(self):
        """Discard all invalid weak references."""
        f = lambda kw: kw[0]() is not None
        self.__observers = dict(filter(f, self.__observers.items()))

    def _getRef(self, observer):
        """Return the weak reference associated to *observer* or None
        if *observer* is not a subscribed observer."""
        for ref, record in self.__observers.items():
            if ref() is observer:
                rvalue = ref ; break
        else:
            rvalue = None
        return rvalue

    def _getRecord(self, observer=None, ref=None):
        """Return the record associated to *observer* or None if no
        record if any match is found."""
        if ref is None:
            if observer is None: raise ValueError(
                "At least an argument is mandatory.")
            else:
                ref = self._getRef(observer)          
        return self.__observers.get(ref, None)

    def deleteLater(self):
        # Clear registered observers prior to deleting the object.
        self.clear()
        super().deleteLater()

    def _debugSiblings(self):
        rvalue = super()._debugSiblings()
        rvalue.update(observers=tuple(self.observers()))
        return rvalue

# -------------------------------------------------------------------

class Observer(QtCore.QObject, Node):

    # FIXME: Add unittest for these signals
    class _InternalQObject(QtCore.QObject):
        observableAdded = QtCore.pyqtSignal(QtCore.QObject)
        observableRemoved = QtCore.pyqtSignal(QtCore.QObject)

    @property
    def observableAdded(self):
        return self.__internal.observableAdded

    @property
    def observableRemoved(self):
        return self.__internal.observableRemoved

    def __init__(self, react=None, hz=None, parent=None):        
        """FIXME: 'hz' defines the refresh frequency; if is is None, refresh is
        immediately done at react time, so that the DelayedReactive actually
        works the same as a ReactiveObject."""
        if not sip.ispycreated(self): 
            QtCore.QObject.__init__(self, parent)
            Node.__init__(self)
        self.__internal = Observer._InternalQObject()
        self.__observed = set()
        self.__queue = set()
        self.__timer = QtCore.QTimer(timeout=self._update)
        self.__hz = None if hz is None else float(hz)
        if self.__hz: self.__timer.start(1000/float(hz))
        self._customreact = assertIsInstance(react, None, collections.Callable)
        
    def __del__(self):
        if not sip.isdeleted(self):
            for obs in self.observed():
                # Notify of the subscribed Observables that they have a None 
                # reference
                if obs is not None: obs._checkRefs()
        Node.__del__(self)

    def observed(self):
        """Return an iterator over the observables it is subscribed to."""
        return (ref() for ref in self.__observed)

    def subscribeTo(self, observable, mode=QtCore.Qt.QueuedConnection,
                    child=False):
        """Subscribe to *observable* in order to react to its
        triggers. Return true if subscription has been done, false
        otherwise."""
        assertIsInstance(observable, Observable)
        rvalue = observable.addObserver(self, mode)
        if rvalue and child: observable.setParent(self)
        return rvalue

    def unsubscribeFrom(self, observable):
        """Unsubscribe from *observable*; return true if subscription
        has been done, false otherwise."""        
        return observable.removeObserver(self) \
            if observable in self.observed() else False

    def clear(self):
        """Unsubscribe from all observed observables."""
        for obs in set(self.observed()):
            obs.removeObserver(self)

    def hz(self):
        """FIXME"""
        return self.__hz

    def queue(self):
        """Return an iterator over the observables that have triggered
        whithout having being reacted yet."""
        return (ref() for ref in self.__queue)

    def _reactSlot(self, observable):
        """Slot attached to the observables' trigger signal."""
        if self.__hz is None:
            self._react(observable)
        elif observable not in self.queue(): 
            self.__queue.add(weakref.ref(observable))
                
    def _react(self, observable):
        """React to the *observable*'s trigger."""
        return self._customreact(self, observable) \
             if self._customreact is not None \
             else None

    def _addObservable(self, observable):
        self.__observed.add(weakref.ref(observable))
        self.observableAdded.emit(observable)

    def _removeObservable(self, observable):
        for ref in self.__observed:
            if ref() is observable:
                # Remove from queue if present
                self.__queue.discard(ref)
                self.__observed.remove(ref)
                self.observableRemoved.emit(observable)
                break

    def _update(self):
        """Force to react to all observables in the queue."""
        for ref in self.__queue.copy():
            self._react(ref())
        self.__queue.clear()

    def _checkRefs(self):
        """Discard all invalid weak references."""
        f = lambda o: o() is not None
        self.__observed = set(filter(f, self.__observed))
        self.__queue = set(filter(f, self.__queue))

    def _debugSiblings(self):
        rvalue = super()._debugSiblings()
        rvalue.update(observed=tuple(self.observed()))
        return rvalue
