# -*- coding: utf-8 -*-
#
# boing/eventloop/StateMachine.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections

from boing.eventloop.OnDemandProduction import OnDemandProducer
from boing.utils.ExtensibleTree import ExtensibleTree

class StateMachine(OnDemandProducer):
    """The StateMachine has a state defined by an ExtensibleTree.
    Everytime the state changes, it produces a diff ExtensibleTree."""

    def __init__(self, initial=None, parent=None):
        OnDemandProducer.__init__(self, 
                                  match=StateMachine._match,
                                  parent=parent)
        self._state = ExtensibleTree(initial)
        
    def state(self):
        """Return the state. Any direct modification won't be reported
        as a state change event."""
        return self._state

    def setState(self, update=None, remove=None, 
                 diff=None, additional=None):
        """Modify the internal state applying 'update', 'remove',
        (which must be flatten trees), and 'diff' (an
        ExtensibleTrees). The diff tree is then posted as a product
        after having being updated with 'additional'."""
        update_tree = remove_tree = None
        if update is not None: update_tree = ExtensibleTree(update)
        if remove is not None: remove_tree = ExtensibleTree(remove)
        if diff is not None:            
            if "updated" in diff:
                if update_tree is not None:
                    set_tree.update(diff.updated)
                elif "added" not in diff: update_tree = diff.updated
                else: update_tree = diff.updated.copy()
            if "added" in diff: 
                if updated_tree is None: updated_tree = diff.added
                else: updated_tree.update(diff.added)
            if "removed" in diff:
                if remove_tree is None: remove_tree = diff.removed
                else: remove_tree.update(diff.removed)
        # Apply diff
        real_diff = None
        if update_tree is not None:
            real_diff = self._state.update(update_tree, getdiff=True)
            if remove_tree is not None:
                real_diff.update(self._state.remove_update(remove_tree, getdiff=True))
        elif remove_tree is not None:
            real_diff = self._state.remove_update(remove_tree, getdiff=True)
        if real_diff: 
            product = ExtensibleTree()
            product.diff = real_diff
            if additional is not None: product.update(additional)
            self._postProduct(product)
        elif additional is not None:
            self._postProduct(ExtensibleTree(additional))

    @staticmethod
    def _match(product, patterns):
        """Return the subtree from 'product' that matches 'patterns'.
        If 'product' is not ExtensibleTree, it is validated only if
        'patterns' is None."""
        if patterns is None: return product
        elif isinstance(product, ExtensibleTree):
            subtree = ExtensibleTree()
            for path in patterns:
                matches = product.match(path)
                if matches is not None: subtree.update(matches, reuse=True)
            return subtree
        elif isinstance(product, collections.Mapping):
            tree = ExtensibleTree(product)
            subtree = ExtensibleTree()
            for path in patterns:
                matches = tree.match(path)
                if matches is not None: subtree.update(matches, reuse=True)
            subproduct = type(product)()
            for key, value in product.items():
                if key in subtree: subproduct[key] = value
            return subproduct
        else:
            return None

# -------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    from boing.eventloop.EventLoop import EventLoop
    from boing.eventloop.OnDemandProduction import SelectiveConsumer
    class DebugConsumer(SelectiveConsumer):
        def _consume(self, products, producer):
            print(self.restrictions(), ": ", 
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
    o1 = DebugConsumer(restrictions=(".*",))
    o1.subscribeTo(stateMachine)
    o2 = DebugConsumer(restrictions=(("diff",".*","gestures",1),))
    o2.subscribeTo(stateMachine)
    o3 = DebugConsumer(restrictions=(("diff","removed"),))
    o3.subscribeTo(stateMachine)
    o4 = DebugConsumer(restrictions=(("diff",".*","gestures",".*", ".*pos.*"),))
    o4.subscribeTo(stateMachine)
    o5 = DebugConsumer(restrictions=(("diff",".*","gestures", 0),"seconds"),
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
    

