# -*- coding: utf-8 -*-
#
# boing/core/observer.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

"""
The observer module provides an implementation of the Observer design
pattern.

Beyond the standard behaviour, this implementation enables the
Observable objects to trigger only a subset of all the current
registered Observer objects.
"""

import collections
import sip
import sys
import weakref

from PyQt4 import QtCore

from boing.core.graph import Node
from boing.utils import assertIsInstance

class Observable(QtCore.QObject, Node):
    """    
    An Observable can be subscribed by a list of Observer objects;
    then the observable can trigger all or a subset of the subscribed
    observers by invoking its method named *trigger*.

    An Observable does not own the subscribed observers, since weak
    references are used.
    """
    
    # FIXME: Add unittest for these signals
    observerAdded = QtCore.pyqtSignal(QtCore.QObject)
    """Signal emitted when a new observer is added."""

    observerRemoved = QtCore.pyqtSignal(QtCore.QObject)
    """Signal emitted when a registered observer is removed."""

    class _ObserverRecord(QtCore.QObject):
        trigger = QtCore.pyqtSignal(QtCore.QObject)
        def __init__(self, observer, mode):
            super().__init__()
            self.trigger.connect(observer._reactSlot, mode)

    def __init__(self, parent=None):
        """
        Constructor.
        
        *parent* defines the observable's parent.
        """
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
        """Subscribe *observer* as a new observer. Return whether
        *observer* has been correctly added. If *child* is true, the
        observer is set to be child of the current observable."""
        assertIsInstance(observer, Observer)
        if observer in self.observers(): 
            rvalue = False
        else:
            observer._Observer__addObservable(self)
            self.__observers[weakref.ref(observer)] = \
                Observable._ObserverRecord(observer, mode)
            if child: observer.setParent(self)
            self.observerAdded.emit(observer)
            rvalue = True
        return rvalue

    def removeObserver(self, observer):
        """Unsubscribe *observer*. Return whether *observer* has been
        correctly removed."""
        ref = self._getRef(observer)
        if ref is None: rvalue = False
        else:
            record = self.__observers.pop(ref)
            record.trigger.disconnect(observer._reactSlot)
            observer._Observer__removeObservable(self)
            if observer.parent() is self: observer.setParent(None)
            self.observerRemoved.emit(observer)
            rvalue = True
        return rvalue

    def clear(self):
        """Unsubscribe all registered observers."""
        for observer in tuple(self.observers()):
            self.removeObserver(observer)

    def notify(self, *restrictions):
        """Trigger all the subscribed observers if *restrictions* is
        empty, otherwise trigger only the registered observers in
        restrictions."""
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
        """Schedules this object for deletion. See Qt docs."""
        # Clear registered observers prior to deleting the object.
        self.clear()
        super().deleteLater()

    def _debugSiblings(self):
        rvalue = super()._debugSiblings()
        rvalue.update(observers=tuple(self.observers()))
        return rvalue

# -------------------------------------------------------------------

class Observer(QtCore.QObject, Node):
    """    
    An observer can subscribe itself to many observables in order to listen
    to their notifications.

    The method *_react* is invoked as consequence of an observable notification.

    It is possible to configure the Observer to immediately react to
    the observer notification, or to enqueue the triggered
    observables and to react at regular time interval.
    
    An Observer does not own the observables it is subscribed to,
    since weak references are used.
    """

    # FIXME: Add unittest for these signals
    class _InternalQObject(QtCore.QObject):
        observableAdded = QtCore.pyqtSignal(QtCore.QObject)
        observableRemoved = QtCore.pyqtSignal(QtCore.QObject)

    @property
    def observableAdded(self):
        """Signal emitted when the observer is subscribed to a new
        observable."""
        return self.__internal.observableAdded

    @property
    def observableRemoved(self):
        """Signal emitted when the observer is unsubscribed from an
        observable."""
        return self.__internal.observableRemoved

    def __init__(self, react=None, hz=None, parent=None):        
        """
        Constructor.
        
        *react* can be a callable object to be used as a handler to the
         observer notifications (see *_react* for the handler arguments)
         or None.

        *hz* defines when the observer should react to the observervables'
         notifications. Accepted values:
          - None   : immediately ;
          - 0      : never ;
          - float  : at the selected frequency (in hz).

        *parent* defines the observer's parent.
        """
        if not sip.ispycreated(self): 
            QtCore.QObject.__init__(self, parent)
            Node.__init__(self)
        self.__internal = Observer._InternalQObject()
        self.__observed = set()
        self.__queue = set()
        self.__timer = QtCore.QTimer(timeout=self._update)
        self.__hz = None if hz is None else float(hz)
        if self.__hz: self.__timer.start(1000/float(hz))
        self.__react = assertIsInstance(react, None, collections.Callable)
        
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
        """Subscribe to *observable*. Return whether *observer* has
        been successfully subscribed to."""
        assertIsInstance(observable, Observable)
        rvalue = observable.addObserver(self, mode)
        if rvalue and child: observable.setParent(self)
        return rvalue

    def unsubscribeFrom(self, observable):
        """Unsubscribe from *observable*. Return whether *observable*
        has been successfully found and removed."""        
        return observable.removeObserver(self) \
            if observable in self.observed() else False

    def clear(self):
        """Unsubscribe from all observed observables."""
        for obs in set(self.observed()):
            obs.removeObserver(self)

    def hz(self):
        """Return when the observer should react to the observers'
         notifications. Possible values:
          - None   : immediately ;
          - 0      : never ;
          - float  : at the selected frequency (in hz)."""
        return self.__hz

    def queue(self):
        """Return an iterator over the observables that have triggered
        without having being reacted to yet."""
        return (ref() for ref in self.__queue)

    def _reactSlot(self, observable):
        """Slot attached to the observables' trigger signal."""
        if self.__hz is None:
            self._react(observable)
        elif observable not in self.queue(): 
            self.__queue.add(weakref.ref(observable))
                
    def _react(self, observable):
        """React to the *observable*'s trigger."""
        return self.__react(self, observable) \
             if self.__react is not None \
             else None

    def __addObservable(self, observable):
        self.__observed.add(weakref.ref(observable))
        self.observableAdded.emit(observable)

    def __removeObservable(self, observable):
        for ref in self.__observed:
            if ref() is observable:
                # Remove from queue if present
                self.__queue.discard(ref)
                self.__observed.remove(ref)
                if observable.parent() is self: observable.setParent(None)
                self.observableRemoved.emit(observable)                
                break

    def _update(self):
        """Require the observer to react to all observables in the queue."""
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
