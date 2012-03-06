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
from boing.eventloop.OnDemandProduction import OnDemandProducer
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

    def setState(self, update=None, remove=None, diff=None, 
                 additional=None):
        """Modify the internal state applying 'update' (a dict),
        'remove' (a set), and 'diff' (an ExtensibleTree). The value of
        diff is consumed. The diff tree is then posted as a product
        after having being updated with 'additional'."""
        if diff is None:
            diff = ExtensibleTree()
            if update is not None: 
                diff.updated = ExtensibleTree(update)
            if remove is not None: 
                diff.removed = ExtensibleTree(dict((k, None) for k in remove))
        elif update is not None or remove is not None:
            raise ValueError("Cannot set both diff and update/remove parameters")
        # Apply diff
        diff = self._applyDiff(diff, self._postdiff)
        if diff:
            product = ExtensibleTree({"diff":diff})
            if additional is not None: product.update(additional)
            self._postProduct(product)

    def _applyDiff(self, diff, getdiff=True):
        """Apply the argument diff to the current state. Return the
        real diff if getdiff is True, otherwise None."""
        rvalue = updatetree = None
        if "added" in diff:                                                         
            updatetree = diff.added                        
        if "updated" in diff:                                                       
            if updatetree is None: 
                updatetree = diff.updated                      
            else: 
                updatetree.update(diff.updated, reuse=True)                      
        if updatetree is not None:
            rvalue = self._state.update(updatetree, reuse=True, getdiff=getdiff)
        if "removed" in diff:
            removed = self._state.remove_update(diff.removed, getdiff)
            if removed:
                if rvalue is None:
                    rvalue = removed
                else:
                    rvalue.update(removed, reuse=True)
        return rvalue

    def _postProduct(self, product):
        if not isinstance(product, collections.Mapping):
            raise TypeError("product must be collections.Mapping, not %s"%
                            product.__class__.__name__)
        fresult = self._applyFunctions(product, self._state)
        if fresult:
            if "diff" in fresult: 
                fresult.diff = self._applyDiff(fresult.diff)
            product.update(fresult, reuse=True)
        OnDemandProducer._postProduct(self, product)

    def _updateOverallDemand(self):
        MappingProducer._updateOverallDemand(self)
        self._postdiff = MappingProducer.matchDemand("diff", self._overalldemand)

# -------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    from boing.eventloop.EventLoop import EventLoop
    from boing.eventloop.OnDemandProduction import SelectiveConsumer
    class DebugConsumer(SelectiveConsumer):
        def _consume(self, products, producer):
            print(self.request(), ": ", 
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
                    remove={("gestures",0)})
    EventLoop.after(9, setState, 
                    remove={("gestures",1)})
    # Run
    print("Initial state:", stateMachine.state().flatten())
    EventLoop.runFor(10)
    print("Final state:", stateMachine.state().flatten())
