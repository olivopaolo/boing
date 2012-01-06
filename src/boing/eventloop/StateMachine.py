# -*- coding: utf-8 -*-
#
# boing/eventloop/StateMachine.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections

from boing.eventloop.MappingEconomy import MappingProducer
from boing.utils.ExtensibleTree import ExtensibleTree

class StateMachine(MappingProducer):
    """The StateMachine has a state defined by an ExtensibleTree.
    Everytime the state changes, it produces a diff ExtensibleTree if
    anyone registered for it."""

    def __init__(self, initial=None, productoffer="diff", parent=None, **kwargs):
        MappingProducer.__init__(self, productoffer, parent=parent)
        self._state = ExtensibleTree(initial)
        self._postdiff = False
        
    def state(self):
        return self._state

    def setState(self, update=None, remove=None, 
                 diff=None, additional=None):
        """Modify the internal state applying 'update', 'remove',
        (which must be mapping types), and 'diff' (an
        ExtensibleTree). The value of diff is consumed. The diff tree
        is then posted as a product after having being updated with
        'additional'."""
        update_tree = remove_tree = real_diff = None
        if update is not None: update_tree = ExtensibleTree(update)
        if remove is not None: remove_tree = ExtensibleTree(remove)
        if diff is not None:
            if "added" in diff: 
                if update_tree is None: update_tree = diff.added
                else: update_tree.update(diff.added, reuse=True)
            if "updated" in diff:
                if update_tree is None: update_tree = diff.updated
                else: update_tree.update(diff.updated, reuse=True)
            if "removed" in diff:
                if remove_tree is None: remove_tree = diff.removed
                else: remove_tree.update(diff.removed, reuse=True)
        # Apply diff
        if update_tree is not None:
            real_diff = self._state.update(update_tree, reuse=True, 
                                           getdiff=self._postdiff)
        if remove_tree is not None:
            remove_diff = self._state.remove_update(remove_tree, 
                                                    getdiff=self._postdiff)
            if real_diff is None:
                real_diff = remove_diff
            else:
                real_diff.update(remove_diff, reuse=True)
        if self._postdiff and real_diff: 
            product = ExtensibleTree()
            product.diff = real_diff
            if additional is not None: product.update(additional)
            self._postProduct(product)

    def _updateOverallDemand(self):
        MappingProducer._updateOverallDemand(self)
        self._postdiff = self.matchDemand("diff")

# -------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    from boing.eventloop.EventLoop import EventLoop
    from boing.eventloop.OnDemandProduction import SelectiveConsumer
    class DebugConsumer(SelectiveConsumer):
        def _consume(self, products, producer):
            print(self.requests(), ": ", 
                  ", ".join(str(p) for p in products))
    def setState(tid, **kwargs):
        stateMachine.setState(**kwargs)
    def incrementTime(tid):
        global seconds ; seconds += 1
        stateMachine._postProduct({"seconds": seconds})
    # Init objects
    seconds = 0
    stateMachine = StateMachine()
    state = stateMachine.state()
    state.gestures = ExtensibleTree()
    o1 = DebugConsumer(requests=".*")
    o1.subscribeTo(stateMachine)
    o2 = DebugConsumer(requests={("diff",".*","gestures",1),
                                 ("diff",".*","gestures",2)})
    o2.subscribeTo(stateMachine)
    o3 = DebugConsumer(requests=("diff","removed"))
    o3.subscribeTo(stateMachine)
    o4 = DebugConsumer(requests=("diff",".*","gestures",".*", ".*pos.*"))
    o4.subscribeTo(stateMachine)
    o5 = DebugConsumer(requests={("diff",".*","gestures", 0),"seconds"},
                       hz=0.1)
    o5.subscribeTo(stateMachine)
    EventLoop.repeat_every(1, incrementTime)
    EventLoop.after(2, setState, update={("gestures",0,"pos"):(0,0)})
    EventLoop.after(3, setState, update={("gestures",0,"pos"):(1,2)})
    EventLoop.after(4, setState, 
                    update={("gestures",0,"pos"):(1,3),
                            ("gestures",1):ExtensibleTree({"pos":(3,3)})})
    EventLoop.after(5, setState, 
                    update={("gestures",0,"pos"):(1,3),
                            ("gestures",1,"pos"):(3,5)})
    EventLoop.after(6, setState, update={("gestures",0,"pos"):(1,3)})
    EventLoop.after(7, setState, 
                    remove={("gestures",0):None,})
    EventLoop.after(9, setState, 
                    remove={("gestures",1):None,})
    # Run
    print("Initial state:", stateMachine.state().flatten())
    EventLoop.runFor(10)
    print("Final state:", stateMachine.state().flatten())
    

