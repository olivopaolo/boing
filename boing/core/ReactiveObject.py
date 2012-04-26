# -*- coding: utf-8 -*-
#
# boing/core/ReactiveObject.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import weakref

from PyQt4 import QtCore

class Observable(QtCore.QObject):
    """An Observable can trigger a list of registered ReactiveObjects."""

    # trigger signal
    trigger = QtCore.pyqtSignal(QtCore.QObject)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__observers = set()

    def __del__(self):
        for ref in self.__observers:
            # Notify of the subscribed ReactiveObjects that they have a None 
            # reference
            reactiveobject = ref()
            if reactiveobject is not None:
                try:
                    self.trigger.disconnect(reactiveobject._react)
                except TypeError: pass
                reactiveobject._checkRef()
        # Unless the __del__ method may not be invoked
        for child in tuple(self.children()):
            child.setParent(None)

    def observers(self):
        """Return an iterator over the current observing ReactiveObject."""
        return (ref() for ref in self.__observers)

    def addObserver(self, reactiveobject, mode=QtCore.Qt.QueuedConnection):
        """Return True if the reactiveobject has been correctly registered
        to observe the triggered signals; False otherwise."""
        if not isinstance(reactiveobject, ReactiveObject) \
          or reactiveobject in self.observers():
            return False
        else:
            self.__observers.add(weakref.ref(reactiveobject))
            reactiveobject._addObservable(self)
            self.trigger.connect(reactiveobject._react, mode)
            return True

    def removeObserver(self, reactiveobject):
        """Return True if the reactiveobject has been found and removed;
        False otherwise."""
        for ref in self.__observers:
            if ref() is reactiveobject:
                self.trigger.disconnect(reactiveobject._react)
                reactiveobject._removeObservable(self)
                self.__observers.remove(ref)
                return True
        else: return False

    def clearObservers(self):
        """Remove all registered observers."""
        for reactiveobject in self.observers():
            self.trigger.disconnect(reactiveobject._react)
            reactiveobject._removeObservable(self)
        self.__observers.clear()

    @QtCore.pyqtSlot()
    def notifyObservers(self):
        """Invoke the method "_react" of all the registered ReactiveObjects."""
        self.trigger.emit(self)
            
    def _checkRef(self):
        # Keep only alive references
        self.__observers = set(ref for ref in self.__observers \
                                   if ref() is not None)

    def deleteLater(self):
        self.clearObservers()
        QtCore.QObject.deleteLater(self)
 

class ReactiveObject(object):
    """Object that can register to different Observables, in order to listen to
    their notifications."""
    def __init__(self):
        self.__observed = set()
        
    def __del__(self):
        for observable in self.observed():
            # Notify of the subscribed Observables that they have a None 
            # reference
            if observable is not None: observable._checkRef()

    def observed(self):
        """Return an iterator over the current observed Observables."""
        return (ref() for ref in self.__observed)

    def subscribeTo(self, observable, mode=QtCore.Qt.QueuedConnection):
        if isinstance(observable, Observable):            
            return observable.addObserver(self, mode)
        else: return False

    def unsubscribeFrom(self, observable):
        if isinstance(observable, Observable):            
            return observable.removeObserver(self)
        else: return False

    def clearObserved(self):
        for observable in tuple(self.observed()):
            observable.removeObserver(self)
    
    def _addObservable(self, observable):
        """It can be overridden, but do not invoke it directly."""
        self.__observed.add(weakref.ref(observable))

    def _removeObservable(self, observable):
        """It can be overridden, but do not invoke it directly."""
        for ref in self.__observed:
            if ref() is observable: 
                self.__observed.remove(ref) ; 
                break

    def _checkRef(self):
        # Keep only alive references
        self.__observed = set(ref for ref in self.__observed \
                                  if ref() is not None)

    def _react(self, observable):
        """It can be overridden to define business logic, but do not invoke it
        directly."""
        pass


class DelayedReactive(ReactiveObject):
    """A ReactiveObject that postpones the reaction to an Observable
    notification to a fixed refresh time. All the Observable that have been
    notified since last refresh are enqueued into the 'queue'."""

    def __init__(self, hz=None):
        """'hz' defines the refresh frequency; if is is None, refresh is
        immediately done at react time, so that the DelayedReactive actually
        works the same as a ReactiveObject."""
        ReactiveObject.__init__(self)
        self.__hz = None if hz is None else float(hz)
        if self.__hz: 
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.__timeout)
            self.timer.start(1000/hz)
        self.__queue = set()

    def frequency(self):
        return self.__hz

    def queue(self):
        """Iterator over the Observables that have notified since last
        refresh."""
        return (ref() for ref in self.__queue)

    def _react(self, observable):
        if observable not in self.queue(): 
            self.__queue.add(weakref.ref(observable))
        if self.__hz is None:
            self._refresh()
            self.__queue.clear()

    def _removeObservable(self, observable):
        """It can be overridden, but do not invoke it directly."""
        ReactiveObject._removeObservable(self, observable)
        for ref in self.__queue:
            if ref() is observable: 
                self.__queue.remove(ref) ; break

    def _checkRef(self):
        ReactiveObject._checkRef(self)
        # Keep only alive references
        self.__queue = set(ref for ref in self.__queue if ref() is not None)

    def __timeout(self):
        if self.__queue:
            self._refresh()
            self.__queue.clear()

    def _refresh(self):
        """It can be overridden to define business logic, but do not invoke it
        directly."""
        pass

# -------------------------------------------------------------------

if __name__ == '__main__':
    import itertools
    import signal
    import sys
    if len(sys.argv)<2 or not sys.argv[1].isdecimal():
        print("usage: %s <seconds>"%sys.argv[0])
        sys.exit(1)
    class DebugReactive(ReactiveObject):
        def _react(self, obs):
            print("%s reacted to %s"%(self.name, obs.name))
    class DebugDelayedReactive(DelayedReactive):
        def _refresh(self):
            names = []
            for i in self.queue():
                names.append(i.name)
            print("%s refresh to"%self.name, names)
    # Init app
    app = QtCore.QCoreApplication(sys.argv)
    signal.signal(signal.SIGINT, lambda *args: app.quit())
    QtCore.QTimer.singleShot(int(sys.argv[1])*1000, app.quit)
    # Init observables
    obs = []
    for i, period in enumerate((300,700)):
        o = Observable()
        o.name = "o%d"%(i+1)
        tid = QtCore.QTimer(o)
        tid.timeout.connect(o.notifyObservers)
        tid.start(period)
        obs.append(o)
    # Init ReactiveObjects
    reacts = list()
    reacts.append(DebugReactive())
    reacts.append(DebugDelayedReactive(1))
    reacts.append(DebugDelayedReactive(None))
    for i, r in enumerate(reacts):
        r.name = "r%d"%(i+1)
    # Full subscription
    for o, r in itertools.product(obs, reacts): 
        r.subscribeTo(o)
    del o, r
    # Run
    sys.exit(app.exec_())

