# -*- coding: utf-8 -*-
#
# boing/eventloop/StateMachine.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import copy

from boing.eventloop.MappingEconomy import Node
from boing.utils import quickdict

class StateMachine(object):
    """It has a dictionary as state."""
    def __init__(self, initial=None):
        self._state = quickdict(initial) \
            if isinstance(initial, collections.Mapping) \
            else quickdict()
        
    def state(self):
        return self._state

    def setState(self, add=None, update=None, remove=None):
        diff = quickdict()
        if add is not None: diff.added = add
        if update is not None: diff.updated = update
        if remove is not None: diff.removed = remove
        self.applyDiff(diff)

    def applyDiff(self, diff, feedback=False):
        rvalue = None
        if feedback:
            rvalue = quickdict()
            if "added" in diff:
                added = StateMachine.add(self._state, diff["added"], True)
                if added is not None: rvalue.added = added
            if "updated" in diff:
                updated = StateMachine.update(self._state, diff["updated"], True)
                if updated is not None: rvalue.updated = updated
            if "removed" in diff:
                removed = StateMachine.remove(self._state, diff["removed"], True)
                if removed is not None: rvalue.removed = removed
        else:
            if "added" in diff: StateMachine.add(self._state, diff["added"])
            if "updated" in diff: StateMachine.update(self._state, diff["updated"])
            if "removed" in diff: StateMachine.remove(self._state, diff["removed"])
        return rvalue


    @staticmethod
    def add(obj, other, diff=False):
        rvalue = dict() if diff else None
        for key, value in other.items():
            if key in obj:
                # Inner case
                objvalue = obj[key]
                if isinstance(value, collections.Mapping) \
                        and isinstance(objvalue, collections.Mapping):
                    inner = StateMachine.add(objvalue, value, diff)                  
                    if inner: rvalue[key] = inner
            else:
                obj[key] = copy.deepcopy(value)
                if diff: rvalue[key] = value
        return rvalue

    @staticmethod
    def update(obj, other, diff=False):
        rvalue = dict() if diff else None
        for key, value in other.items():
            if key in obj:
                # Inner case
                objvalue = obj[key]
                if isinstance(value, collections.Mapping) \
                        and isinstance(objvalue, collections.Mapping):
                    inner = StateMachine.update(objvalue, value, diff)
                    if inner: rvalue[key] = inner
                elif objvalue!=value:
                    obj[key] = copy.deepcopy(value)
                    if diff: rvalue[key] = value
            else:
                obj[key] = copy.deepcopy(value)
                if diff: rvalue[key] = value
        return rvalue

    @staticmethod
    def remove(obj, other, diff=False):
        rvalue = dict() if diff else None
        for key, value in other.items():
            if key in obj:
                # Inner case
                objvalue = obj[key]
                if isinstance(value, collections.Mapping) \
                        and isinstance(objvalue, collections.Mapping):
                    inner = StateMachine.remove(objvalue, value, diff)
                    if inner: rvalue[key] = inner
                else:
                    del obj[key]
                    if diff: rvalue[key] = None
        return rvalue

    

class StateNode(Node, StateMachine):
    """Everytime the state changes, the diff is posted as a product."""

    def __init__(self, initial=None, request=None, parent=None):
        #FIXME: set productoffer
        Node.__init__(self, request=request, parent=parent)
        StateMachine.__init__(self, initial)
        self._addTag("diff", {"diff":{"added":{}, "updated":{}, "removed":{}}}, 
                     update=False)
        
    def applyDiff(self, diff, additional=None):
        realdiff = StateMachine.applyDiff(self, diff, self._tag("diff"))
        if realdiff:
            product = quickdict({"diff":diff})
            if additional is not None: product.update(additional)
            self._postProduct(product)


# -------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    from PyQt4 import QtCore
    from boing.eventloop.MappingEconomy import DumpConsumer
    app = QtCore.QCoreApplication(sys.argv)
    QtCore.QTimer.singleShot(10000, app.quit)
    m = StateNode({"contacts":{}})
    obs = []
    obs.append(DumpConsumer("diff"))
    obs.append(DumpConsumer(request="diff.*.contacts.1"))
    obs.append(DumpConsumer(request="diff.removed"))
    for o in obs:        
        o.subscribeTo(m)
        o.dumpdest = True
    QtCore.QTimer.singleShot(
        1000, lambda: m.setState(add={"contacts": {"1": {"pos":(0,0)}}}))
    QtCore.QTimer.singleShot(
        2000, lambda: m.setState(update={"contacts": {"1": {"pos":(1,2)}}}))
    QtCore.QTimer.singleShot(
        3000, lambda: m.setState(add={"contacts": {"3": {"pos":(0,0)}}},
                                 update={"contacts": {"1": {"pos":(12,1)}}}))
    QtCore.QTimer.singleShot(
        5000, lambda: m.setState(update={"contacts": {"3": {"pos":(6,5)}}},
                                 remove={"contacts": {"1": None}}))
    QtCore.QTimer.singleShot(
        7000, lambda: m.setState(remove={"contacts": {"3": None}}))
    # Run
    print("Initial state:", m.state())
    rvalue = app.exec_()
    print("Final state:", m.state())
    sys.exit(rvalue)
