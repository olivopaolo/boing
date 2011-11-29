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
        self.dict = {"i":1, "t":"boing", "l":[1,2,3], "d":{"x":0}}
        self.e = ExtensibleStruct(**self.dict)

    def test_isMutableMapping(self):
        self.assertTrue(isinstance(self.e, collections.MutableMapping))

    def test_constructor_empty(self):
        e = ExtensibleStruct()
        self.assertEqual(dict(e.items()), {})
        self.assertEqual(e.signature(), frozenset())

    def test_constructor_dict(self):
        e = ExtensibleStruct(**self.dict)
        self.assertEqual(dict(e.items()), self.dict)

    def test_copy(self):
        copy = self.e.copy()
        self.assertEqual(dict(copy.items()), self.dict)

    def test_get(self):
        self.assertEqual(self.e.get("i"), self.dict["i"])
        self.assertEqual(self.e.get("t"), self.dict["t"])
        self.assertEqual(self.e.get("l"), self.dict["l"])
        self.assertEqual(self.e.get('default', 0), 0)

    def test_setdefault(self):
        self.assertEqual(self.e.setdefault('i',2), 1)
        self.assertEqual(self.e.setdefault('j',0), 0)
        self.assertRaises(AttributeError, self.e.setdefault, 'setdefault', 0)

    def test_items(self):
        self.assertEqual(dict(self.e.items()), self.dict)
        d = {}
        for key, value in self.e.items():
            d[key] = value
        self.assertEqual(d, self.dict)

    def test_values(self):
        values = []
        for k in self.e.values():
            values.append(k)
        self.assertEqual(len(values), 4)
        self.assertTrue(1 in values)
        self.assertTrue("boing" in values)
        self.assertTrue([1,2,3] in values)
        self.assertTrue({"x":0} in values)

    def test_keys(self):
        keys = set()
        for k in self.e.keys():
            keys.add(k)
        self.assertEqual(keys, self.dict.keys())

    def test_signature(self):
        self.assertEqual(self.e.signature(), self.dict.keys())
        self.assertEqual(self.e.signature(True), 
                         {"i":type(1), "t":type("boing"), 
                          "l":type([]), "d":type({})})

    def test_conformsToSignature(self):
        copy = self.e.copy()
        self.assertTrue(self.e.conformsToSignature(copy.signature()))

    def test__getattr__(self):
        self.assertEqual(self.e.i, 1)
        self.assertEqual(self.e.t, "boing")
        self.assertEqual(self.e.l, [1,2,3])
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
        self.assertEqual(self.e.signature(), {"t", "l", "d"})
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
        self.assertEqual(len(self.e), 4)

    def test__iter__(self):
        keys = set()
        for k in self.e:
            keys.add(k)
        self.assertEqual(keys, self.dict.keys())

    def test__getitem__(self):
        self.assertEqual(self.e["i"], 1)
        self.assertEqual(self.e["t"], "boing")
        self.assertEqual(self.e["l"], [1, 2, 3])
        try:
            self.e["default"]
            self.fail("Exception not Raised")
        except AttributeError: pass

    def test__setitem__(self):
        self.e["i"] = 2
        self.e["j"] = 0
        self.assertEqual(self.e.i, 2)
        self.assertEqual(self.e.j, 0)
        try:
            self.e["setdefault"] = 0
            self.fail()
        except AttributeError: pass
        try:
            self.e[12] = 0
            self.fail()
        except TypeError: pass

    def test__delitem__(self):
        del self.e["i"]
        self.assertEqual(self.e.signature(), {"t", "l", "d"})
        try:
            del self.e["setdefault"]
            self.fail("Exception not Raised")
        except AttributeError: pass
        try:
            del self.e["j"]
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
