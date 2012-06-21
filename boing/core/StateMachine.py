# -*- coding: utf-8 -*-
#
# boing/core/StateMachine.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import copy

from boing import utils

class StateMachine(object):
    """It has a dictionary as state."""
    def __init__(self, initial=None):
        self._state = utils.quickdict(initial) \
            if isinstance(initial, collections.Mapping) \
            else utils.quickdict()
        
    def state(self):
        return self._state

    def setState(self, update=None, add=None, remove=None):
        diff = utils.quickdict()
        if add is not None: diff.added = add
        if update is not None: diff.updated = update
        if remove is not None: diff.removed = remove
        self.applyDiff(diff)

    def applyDiff(self, diff, feedback=False):
        rvalue = None
        if feedback:
            rvalue = utils.quickdict()
            if "added" in diff:
                added = utils.deepadd(self._state, diff["added"], True)
                if added is not None: rvalue.added = added
            if "updated" in diff:
                updated = utils.deepupdate(self._state, diff["updated"], True)
                if updated is not None: rvalue.updated = updated
            if "removed" in diff:
                removed = utils.deepremove(self._state, diff["removed"], True)
                if removed is not None: rvalue.removed = removed
        else:
            if "added" in diff: utils.deepadd(self._state, diff["added"])
            if "updated" in diff: utils.deepupdate(self._state, diff["updated"])
            if "removed" in diff: utils.deepremove(self._state, diff["removed"])
        return rvalue
    
'''
class StateNode(Node, StateMachine):
    """Everytime the state changes, the diff is posted as a product."""

    def __init__(self, initial=None, request=None, parent=None):
        #FIXME: set productoffer
        Node.__init__(self, request=request, parent=parent)
        StateMachine.__init__(self, initial)
        
    def applyDiff(self, diff, additional=None):
        realdiff = StateMachine.applyDiff(self, diff, True)
        if realdiff:
            product = utils.quickdict({"diff":diff})
            if additional is not None: product.update(additional)
            self._postProduct(product)

# -------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    from PyQt4 import QtCore
    from boing.nodes.debug import DumpNode
    app = QtCore.QCoreApplication(sys.argv)
    QtCore.QTimer.singleShot(10000, app.quit)
    m = StateNode({"contacts":{}})
    obs = []
    obs.append(DumpNode("diff"))
    obs.append(DumpNode(request="diff.*.contacts.1"))
    obs.append(DumpNode(request="diff.removed"))
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
'''
