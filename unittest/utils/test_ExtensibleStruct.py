#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# test/eventloop/test_ExtensibleEvent.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import unittest

from boing.utils.ExtensibleStruct import ExtensibleStruct

class TestExtensibleStruct(unittest.TestCase):

    def setUp(self):
        self.e = ExtensibleStruct(i=1, t="boing", l=[])

    def test_constructor_empty(self):
        e = ExtensibleStruct()
        self.assertEqual(e.getInfo(), {})
        self.assertEqual(e.getSignature(), frozenset())

    def test_constructor_direct(self):
        e = ExtensibleStruct(i=1, t="boing", l=[])
        self.assertEqual(e.getInfo(), {"i":1, "t":"boing", "l":[]})

    def test_constructor_dict(self):
        mould = {"i":1, "t":"boing", "l":[]} 
        e = ExtensibleStruct(**mould)
        self.assertEqual(e.getInfo(), mould)

    def test_duplicate(self):
        copy = self.e.duplicate()
        self.assertEqual(copy.getInfo(), {"i":1, "t":"boing", "l":[]})

    def test_readattr(self):
        self.assertEqual(self.e.i, 1)
        self.assertEqual(self.e.t, "boing")
        self.assertEqual(self.e.l, [])
        try:
            self.e.x
            self.fail()
        except AttributeError: pass
    
    def test_setattr(self):
        self.e.i = 2
        self.e.j = 0
        self.assertEqual(self.e.i, 2)
        self.assertEqual(self.e.j, 0)
        try:
            self.e.setdefault = 0
            self.fail()
        except AttributeError: pass
        try:
            self.e._ExtensibleStruct__info = 0
            self.fail()
        except AttributeError: pass

    def test_get(self):
        self.assertEqual(self.e.get("i"), 1)
        self.assertEqual(self.e.get("t"), "boing")
        self.assertEqual(self.e.get("l"), [])
        self.assertEqual(self.e.get('default', 0), 0)

    def test_set(self):
        self.e.set('i', 2) 
        self.assertEqual(self.e.i, 2)
        self.e.set('j', 0)
        self.assertEqual(self.e.j, 0)
        self.assertRaises(AttributeError, self.e.set, 'setdefault', 0)
        self.assertRaises(TypeError, self.e.set, None, 0)

    def test_setdefault(self):
        self.assertEqual(self.e.setdefault('i',2), 1)
        self.assertEqual(self.e.setdefault('j',0), 0)
        self.assertRaises(AttributeError, self.e.setdefault, 'setdefault', 0)

    def test_getInfo(self):
        self.assertEqual(self.e.getInfo(), {"i":1, "t":"boing", "l":[]})

    def test_getSignature(self):
        self.assertEqual(self.e.getSignature(), {"i","t","l"})
        self.assertEqual(self.e.getSignature(True), 
                         {"i":type(1), "t":type("boing"), "l":type([])})

    def test_conformsToSignature(self):
        copy = self.e.duplicate()
        self.assertTrue(self.e.conformsToSignature(copy.getSignature()))

    def test_equality(self):
        e1 = ExtensibleStruct(x=0, y="word", 
                              friends=[None],
                              dict_={"x":None},
                              inner=ExtensibleStruct(x=0))
        e2 = ExtensibleStruct(x=0, y="word", 
                              friends=[None], 
                              dict_={"x":None},
                              inner=ExtensibleStruct(x=0))
        self.assertTrue(e1==e2)
        self.assertFalse(e1!=e2)
        self.assertEqual(e1,e2)
 
    def test_disequality(self):
        e1 = ExtensibleStruct(x=0, pos=(0.14514, 0.123213))
        e2 = ExtensibleStruct(x=0, pos=(0.32322, 0.213222))
        e3 = ExtensibleStruct(x=0, y=0, z=0)
        self.assertTrue(e1!=e2)
        self.assertFalse(e1==e2)
        self.assertTrue(e1!=e3)
        self.assertFalse(e1==e3)
        self.assertNotEqual(e1,e2)
        self.assertNotEqual(e1,e3)
        
# -------------------------------------------------------------------

def suite():
    tests = list(t for t in TestExtensibleStruct.__dict__ \
                   if t.startswith("test_"))
    return unittest.TestSuite(list(map(TestExtensibleStruct, tests)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
