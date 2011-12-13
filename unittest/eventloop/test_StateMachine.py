#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# unittest/eventloop/test_StateMachine.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from datetime import datetime
import unittest, weakref

from boing.eventloop.EventLoop import EventLoop
from boing.eventloop.StateMachine import StateMachine
from boing.eventloop.OnDemandProduction import SelectiveConsumer
from boing.utils.ExtensibleTree import ExtensibleTree

class ConcatenateConsumer(SelectiveConsumer):
    def __init__(self, testcase, target):
        SelectiveConsumer.__init__(self)
        self.test = testcase
        self.target = target
        
    def _consume(self, products, producer):
        diff = ExtensibleTree()
        for p in products:
            if "diff" in p: self.target.setState(diff=p["diff"])
        self.test.assertEqual(producer.state(), self.target.state())

def incrementTime(tid, m):
    m.setState(additional={"timetag": datetime.now()})

def setState(tid, m, **kwargs):
    m.setState(**kwargs)

class TestStateMachine(unittest.TestCase):

    def test_concatenatedStateMachine(self):
        m1 = StateMachine()
        m2 = StateMachine()
        m3 = StateMachine()
        c = ConcatenateConsumer(self, m2)
        c.subscribeTo(m1)
        c2 = ConcatenateConsumer(self, m3)
        c2.subscribeTo(m2)
        EventLoop.repeat_every(1, incrementTime, m1)
        EventLoop.after(2, setState, m1, update={("gestures",0,"pos"):(0,0)})
        EventLoop.after(3, setState, m1, update={("gestures",0,"pos"):(1,2)})
        EventLoop.after(4, setState, m1,
                        update={("gestures",0,"pos"):(1,3),
                                ("gestures",1):ExtensibleTree({"pos":(3,3)})})
        EventLoop.after(5, setState, m1,
                        update={("gestures",0,"pos"):(1,3),
                                ("gestures",1,"pos"):(3,5)})
        EventLoop.after(7, setState, m1,
                        remove={("gestures",0):None,})
        EventLoop.after(9, setState, m1,
                        remove={("gestures",1):None,})
        EventLoop.runFor(10)


# -------------------------------------------------------------------

def suite():    
    tests = list(t for t in TestStateMachine.__dict__ \
                   if t.startswith("test_"))
    return unittest.TestSuite(map(TestStateMachine, tests))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
