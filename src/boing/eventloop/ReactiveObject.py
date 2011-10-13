# -*- coding: utf-8 -*-
#
# boing/eventloop/ReactiveObject.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import weakref

from PyQt4 import QtCore

from boing.eventloop.EventLoop import EventLoop

class Observable(QtCore.QObject):
    """An Observable can trigger a list of registered ReactiveObjects."""

    # trigger signal
    trigger = QtCore.pyqtSignal(QtCore.QObject)
    
    def __init__(self):
        super().__init__()
        self.__observers = set()
        
    def __del__(self):
        for reactiveobject in self.observers:
            # Notify of the subscribed ReactiveObjects that they have a None 
            # reference
            reactiveobject._checkref()
            self.trigger.disconnect(reactiveobject._react)

    @property
    def observers(self):
        """Return the frozenset of the current observing ReactiveObject."""
        # Return referents not references
        return frozenset(ref() for ref in self.__observers)

    def add_observer(self, reactiveobject):
        if isinstance(reactiveobject, ReactiveObject) \
          and reactiveobject not in self.observers:
            self.__observers.add(weakref.ref(reactiveobject))
            reactiveobject._add_observable(self)
            self.trigger.connect(reactiveobject._react, 
                                 QtCore.Qt.QueuedConnection)

    def remove_observer(self, reactiveobject):
        for ref in self.__observers:
            if ref()==reactiveobject:
                reactiveobject._remove_observable(self)
                self.trigger.disconnect(reactiveobject._react)
                self.__observers.remove(ref)
                break

    def notify_observers(self):
        """Invoke the method "_react" of all the registered ReactiveObjects."""
        self.trigger.emit(self)

    def _checkref(self):
        # Keep only alive references
        self.__observers = set(ref for ref in self.__observers \
                                   if ref() is not None)
        

class ReactiveObject(QtCore.QObject):
    """Object that can register to different Observables, in order to listen to
    their notifications."""
    def __init__(self):
        super().__init__()
        self.__observed = set()
        
    def __del__(self):
        for observable in self.observed:
            # Notify of the subscribed Observables that they have a None 
            # reference
            observable._checkref()

    @property
    def observed(self):
        """Return the frozenset of the current subscribed Observables."""
        # Return referents not references
        return frozenset(ref() for ref in self.__observed)

    def subscribe_to(self, observable):
        observable.add_observer(self)

    def unsubscribe_from(self, observable):
        observable.remove_observer(self)

    def _add_observable(self, observable):
        """It can be overridden, but do not invoke it directly."""
        self.__observed.add(weakref.ref(observable))

    def _remove_observable(self, observable):
        """It can be overridden, but do not invoke it directly."""
        for ref in self.__observed:
            if ref()==observable: 
                self.__observed.remove(ref) ; 
                break

    @QtCore.pyqtSlot(Observable)    
    def _react(self, observable):
        """It can be overridden to define business logic, but do not invoke it
        directly."""
        pass

    def _checkref(self):
        # Keep only alive references
        self.__observed = set(ref for ref in self.__observed \
                                  if ref() is not None)


class DelayedReactive(ReactiveObject):
    """A ReactiveObject that postpones the reaction to an Observable
    notification to a fixed refresh time. All the Observable that have been
    notified since last refresh are enqueued into the 'queue'."""

    def __init__(self, hz=None):
        """'hz' defines the refresh frequency; if is is None, refresh is
        immediately done at react time, so that the DelayedReactive actually
        works the same as a ReactiveObject."""
        super().__init__()
        self.__hz = hz
        if hz is None or float(hz)==0: self.__tid = None
        else: self.__tid = EventLoop.repeat_every(1/hz, 
                                                  DelayedReactive._timeout,
                                                  weakref.ref(self))
        self.__queue = set()

    @property
    def frequency(self):
        return self.__hz

    @property
    def queue(self):
        """List of Observables that has notified since last refresh."""
        # Return referents not references
        return frozenset(ref() for ref in self.__queue)

    def _react(self, observable):
        if observable not in self.queue: 
            self.__queue.add(weakref.ref(observable))
        if self.__hz is None:
            self._refresh()
            self.__queue = set()

    def _remove_observable(self, observable):
        """It can be overridden, but do not invoke it directly."""
        super()._remove_observable(observable)
        if observable in self.queue: 
             self.__queue = set(ref for ref in self.__queue \
                                    if ref() is not None and ref()!=observable)

    def _refresh(self):
        """It can be overridden to define business logic, but do not invoke it
        directly."""
        pass

    def _checkref(self):
        super()._checkref()
        # Keep only alive references
        self.__queue = set(ref for ref in self.__queue if ref() is not None)

    @staticmethod
    def _timeout(tid, ref):
        o = ref()
        if o is None: EventLoop.cancel_timer(tid)
        elif o._DelayedReactive__queue:
            o._refresh()
            o._DelayerReactive__queue = set()

# -------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    if len(sys.argv)<2:
        print("Usage: %s seconds"%sys.argv[0])
        sys.exit(1)
    class DebugReactive(ReactiveObject):
        def _react(self, obs):
            print("%s reacted to %s"%(self.name, obs.name))
    class DebugDelayedReactive(DelayedReactive):
        def _refresh(self):
            names = []
            for i in self.queue:
                names.append(i.name)
            print("%s refresh to"%self.name, names)
    def notify(tid, obs, *args, **kwargs):
        obs.notify_observers()
    # Init observables
    o1 = Observable()
    o2 = Observable()
    o1.name = "o1"
    o2.name = "o2"
    # Init ReactiveObjects
    r1 = DebugReactive()
    r2 = DebugDelayedReactive(1)
    r3 = DebugDelayedReactive(None)
    r1.name = "r1"
    r2.name = "r2"
    r3.name = "r3"
    r1.subscribe_to(o1)
    r1.subscribe_to(o2)
    r2.subscribe_to(o1)
    r2.subscribe_to(o2) 
    r3.subscribe_to(o1)
    r3.subscribe_to(o2)
    # run
    t_o1 = EventLoop.repeat_every(0.4, notify, o1)
    t_o2 = EventLoop.repeat_every(0.7, notify, o2)
    EventLoop.run_for(int(sys.argv[1]))
