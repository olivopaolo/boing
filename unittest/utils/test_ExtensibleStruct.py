#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# test/eventloop/test_ExtensibleEvent.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import unittest

from boing.utils.ExtensibleStruct import ExtensibleStruct

class TestExtensibleStruct(unittest.TestCase):

    def setUp(self):
        self.e = ExtensibleStruct(i=1, t="boing", l=[])

    def test_isMutableMapping(self):
        self.assertTrue(isinstance(self.e, collections.MutableMapping))

    def test_constructor_empty(self):
        e = ExtensibleStruct()
        self.assertEqual(dict(e.items()), {})
        self.assertEqual(e.signature(), frozenset())

    def test_constructor_direct(self):
        e = ExtensibleStruct(i=1, t="boing", l=[])
        self.assertEqual(dict(e.items()), {"i":1, "t":"boing", "l":[]})

    def test_constructor_dict(self):
        mould = {"i":1, "t":"boing", "l":[]} 
        e = ExtensibleStruct(**mould)
        self.assertEqual(dict(e.items()), mould)

    def test_copy(self):
        copy = self.e.copy()
        self.assertEqual(dict(copy.items()), {"i":1, "t":"boing", "l":[]})

    def test_get(self):
        self.assertEqual(self.e.get("i"), 1)
        self.assertEqual(self.e.get("t"), "boing")
        self.assertEqual(self.e.get("l"), [])
        self.assertEqual(self.e.get('default', 0), 0)

    def test_setdefault(self):
        self.assertEqual(self.e.setdefault('i',2), 1)
        self.assertEqual(self.e.setdefault('j',0), 0)
        self.assertRaises(AttributeError, self.e.setdefault, 'setdefault', 0)

    def test_items(self):
        self.assertEqual(dict(self.e.items()), {"i":1, "t":"boing", "l":[]})
        d = {}
        for key, value in self.e.items():
            d[key] = value
        self.assertEqual(d, {"i":1, "t":"boing", "l":[]})

    def test_values(self):
        values = []
        for k in self.e.values():
            values.append(k)
        self.assertEqual(len(values), 3)
        self.assertTrue(1 in values)
        self.assertTrue("boing" in values)
        self.assertTrue([] in values)

    def test_keys(self):
        keys = set()
        for k in self.e.keys():
            keys.add(k)
        self.assertEqual(keys, {"i", "t", "l"})

    def test_signature(self):
        self.assertEqual(self.e.signature(), {"i","t","l"})
        self.assertEqual(self.e.signature(True), 
                         {"i":type(1), "t":type("boing"), "l":type([])})

    def test_conformsToSignature(self):
        copy = self.e.copy()
        self.assertTrue(self.e.conformsToSignature(copy.signature()))

    def test__getattr__(self):
        self.assertEqual(self.e.i, 1)
        self.assertEqual(self.e.t, "boing")
        self.assertEqual(self.e.l, [])
        try:
            self.e.x
            self.fail()
        except AttributeError: pass
    
    def test__setattr__(self):
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

    def test__delattr__(self):
        del self.e.i
        self.assertEqual(self.e.signature(), {"t", "l"})
        try:
            del self.e.setdefault
            self.fail("Exception not Raised")
        except AttributeError: pass

    def test__eq__(self):
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
 
    def test__ne__(self):
        e1 = ExtensibleStruct(x=0, pos=(0.14514, 0.123213))
        e2 = ExtensibleStruct(x=0, pos=(0.32322, 0.213222))
        e3 = ExtensibleStruct(x=0, y=0, z=0)
        self.assertTrue(e1!=e2)
        self.assertFalse(e1==e2)
        self.assertTrue(e1!=e3)
        self.assertFalse(e1==e3)
        self.assertNotEqual(e1,e2)
        self.assertNotEqual(e1,e3)

    # ---------------------------------------------------------------------
    #  Emulating container type   

    def test__len__(self):
        self.assertEqual(len(self.e), 3)

    def test__iter__(self):
        keys = set()
        for k in self.e:
            keys.add(k)
        self.assertEqual(keys, {"i", "t", "l"})

    def test__getitem__(self):
        self.assertEqual(self.e["i"], 1)
        self.assertEqual(self.e["t"], "boing")
        self.assertEqual(self.e["l"], [])
        try:
            self.e["default"]
            self.fail("Exception not Raised")
        except KeyError: pass

    def test__setitem__(self):
        self.e["i"] = 2
        self.e["j"] = 0
        self.assertEqual(self.e.i, 2)
        self.assertEqual(self.e.j, 0)
        try:
            self.e["setdefault"] = 0
            self.fail()
        except AttributeError: pass

    def test__delitem__(self):
        del self.e["i"]
        self.assertEqual(self.e.signature(), {"t", "l"})
        try:
            del self.e["setdefault"]
            self.fail("Exception not Raised")
        except AttributeError: pass

    def test__contains__(self):
        self.assertTrue("i" in self.e)
        self.assertFalse("setdefault" in self.e)
        
# -------------------------------------------------------------------

def suite():
    tests = list(t for t in TestExtensibleStruct.__dict__ \
                   if t.startswith("test_"))
    return unittest.TestSuite(list(map(TestExtensibleStruct, tests)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
