# -*- coding: utf-8 -*-
#
# boing/eventloop/StateMachine.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from boing.eventloop.OnDemandProduction import OnDemandProducer
from boing.utils.ExtensibleTree import ExtensibleTree

class StateMachine(OnDemandProducer):
    """The StateMachine has a state defined by an ExtensibleTree.
    Everytime the state changes, it produces a diff ExtensibleTree."""

    def __init__(self, parent=None):
        OnDemandProducer.__init__(self, 
                                  match=StateMachine._match,
                                  parent=parent)
        self._state = ExtensibleTree()
        
    def state(self):
        """Return the state. Any direct modification won't be reported
        as a state change event."""
        return self._state

    def setState(self, update=None, remove=None, add=None, 
                 diff=None, additional=None):
        """Modify the internal state applying 'update', 'remove',
        'add' (which must be flatten trees), and 'diff' (an
        ExtensibleTrees). The diff tree is then posted as a product
        after having being updated with 'additional'."""
        set_tree = ExtensibleTree(update)
        if add: set_tree.update(ExtensibleTree(add))
        remove_tree = ExtensibleTree(remove)
        if diff:
            if "updated" in diff: set_tree.update(diff.updated)
            if "added" in diff: set_tree.update(diff.added)
            if "removed" in diff: remove_tree.update(diff.removed)
        diff = self._state.update(set_tree, True)
        diff.update(self._state.remove(remove_tree, True))
        if diff: 
            product = ExtensibleTree()
            product.diff = diff
            if additional: product.update(additional)
            self._postProduct(product)
        elif additional:
            product = ExtensibleTree(additional)
            self._postProduct(product)            

    @staticmethod
    def _match(product, patterns):
        """Return the subtree from 'product' that matches 'patterns'.
        If 'product' is not ExtensibleTree, it is validated only if
        'patterns' is None."""
        if patterns is None:
            return product
        elif isinstance(product, ExtensibleTree):
            subtree = ExtensibleTree()
            for path in patterns:
                matches = product.match(path, forced=True)
                if matches: subtree.update(matches)
            return subtree
        else:
            return None

    @staticmethod
    def mergeDiff(previous, news):
        """Merge the diff ExtensibleTree 'news' into 'previous'."""
        if not isinstance(previous, ExtensibleTree):
            raise TypeError("Argument 'previous' must be ExtensibleTree, not %s"%
                            previous.__class__.__name__)
        if not isinstance(news, ExtensibleTree):
            raise TypeError("Argument 'news' must be ExtensibleTree, not %s"%
                            news.__class__.__name__)
        previous.update(news)
        if "removed" in news:
            if "updated" in previous: 
                # Remove from updated the removed items
                previous.updated.difference_update(news.removed)
                if not previous.updated: del previous.updated
            if "added" in previous:
                # if an item has not been seen as added, it is
                # possible to remove it from both added and removed
                paths = news.removed.paths()
                for p in paths:
                    matches = previous.added.match(p)
                    if matches:
                        previous.added.difference_update(matches)
                        previous.removed.difference_update(matches)
                if not previous.added: del previous.added
                if not previous.removed: del previous.removed                        

# -------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    from boing.eventloop.EventLoop import EventLoop
    from boing.eventloop.OnDemandProduction import SelectiveConsumer
    class DebugConsumer(SelectiveConsumer):
        def _consume(self, products, producer):
            if len(products)>1:
                # Merge diff
                diff = ExtensibleTree()
                for p in tuple(products):
                    if "diff" in p:
                        if set(p.keys())==set(("diff",)): 
                            local = p.diff
                            products.remove(p)
                        else: local = p.pop("diff")                            
                        StateMachine.mergeDiff(diff, local)
                if diff: products.append(diff)
            print(self.restrictions(), ": [", 
                  ", ".join((str(p) for p in products)), "]")
    def setState(tid, **kwargs):
        stateMachine.setState(**kwargs)
    def incrementTime(tid):
        global seconds ; seconds += 1
        stateMachine._postProduct(ExtensibleTree({"seconds": seconds}))
    # Init objects
    seconds = 0
    stateMachine = StateMachine()
    stateMachine.state().seconds = 0
    stateMachine.state().gestures = ExtensibleTree()
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
    EventLoop.after(2, setState, add={("gestures",0,"pos"):(0,0)})
    EventLoop.after(3, setState, update={("gestures",0,"pos"):(1,2)})
    EventLoop.after(4, setState, 
                    update={("gestures",0,"pos"):(1,3)},
                    add={("gestures",1):ExtensibleTree({"pos":(3,3)})})
    EventLoop.after(5, setState, 
                    update={("gestures",0,"pos"):(1,3),
                            ("gestures",1,"pos"):(3,5)})
    EventLoop.after(7, setState, 
                    remove={("gestures",0):None,})
    EventLoop.after(9, setState, 
                    remove={("gestures",1):None,})
    # Run
    print("Initial state:", stateMachine.state().flatten())
    EventLoop.runFor(10)
    print("Final state:", stateMachine.state().flatten())
    

