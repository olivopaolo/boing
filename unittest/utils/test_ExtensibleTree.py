#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# test/utils/test_ExtensibleTree.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import unittest

from boing.utils.ExtensibleTree import ExtensibleTree

class TestExtensibleTree(unittest.TestCase):

    def setUp(self):
        self.dict = {1:1,
                     "i":1,
                     "t":"boing", 
                     "l":[1,2,3,"text"], 
                     "d":{"x":0, "i":1, 1:"iid", 2:"iid"}}
        self.e = ExtensibleTree(self.dict)

    def test_isMutableMapping(self):
        e = ExtensibleTree()
        self.assertTrue(isinstance(e, collections.MutableMapping))

    def test_constructor_empty(self):
        e = ExtensibleTree()
        self.assertEqual(dict(e.items()), {})

    def test_constructor_dict(self):
        e = ExtensibleTree(self.dict)
        self.assertEqual(dict(e.items()), self.dict)

    def test__getattr__(self):
        e = ExtensibleTree(self.dict)
        self.assertEqual(e.i, self.dict["i"])
        self.assertEqual(e.t, self.dict["t"])
        self.assertEqual(e.l, self.dict["l"])
    
    def test__setattr__(self):
        e = ExtensibleTree(self.dict)
        e.i = 2
        e.j = 0
        self.assertEqual(e.i, 2)
        self.assertEqual(e.j, 0)
        self.assertRaises(AttributeError, setattr, e, "update", 0)
        self.assertRaises(AttributeError, setattr, e, "_ExtensibleTree__info", 0)

    def test__delattr__(self):
        e = ExtensibleTree(self.dict)
        del e.i
        self.assertEqual(set(e.keys()), {1, "t", "l", "d"})
        self.assertRaises(AttributeError, delattr, e, "noattr")
        self.assertRaises(AttributeError, delattr, e, "update")
        self.assertRaises(AttributeError, delattr, e, "clear")
        self.assertRaises(AttributeError, delattr, e, "_ExtensibleTree__info")

    def test_keys(self):
        self.e[1] = 6
        self.dict[1] = 6
        keys = set()
        for k in self.e.keys():
            keys.add(k)
        self.assertEqual(keys, self.dict.keys())

    def test_values(self):
        self.e[1] = 6
        self.dict[1] = 6
        values = []
        for k in self.e.values():
            values.append(k)
        self.assertEqual(len(values), 5)
        self.assertTrue(self.dict["i"] in values)
        self.assertTrue(self.dict["t"] in values)
        self.assertTrue(self.dict["l"] in values)
        self.assertTrue(self.dict["d"] in values)
        self.assertTrue(self.dict[1] in values)

    def test_items(self):
        self.e[1] = 6
        self.dict[1] = 6
        self.assertEqual(dict(self.e.items()), self.dict)
        d = {}
        for key, value in self.e.items():
            d[key] = value
        self.assertEqual(d, self.dict)

    def test_match(self):
        self.e.e = ExtensibleTree(self.dict)
        self.assertTrue(self.e.match("i"))
        self.assertFalse(self.e.match("j"))
        self.assertTrue(self.e.match(1))
        self.assertFalse(self.e.match(2))
        self.assertTrue(self.e.match("."))
        self.assertTrue(self.e.match("i*"))
        self.assertTrue(self.e.match(".*"))
        self.assertFalse(self.e.match("j*"))
        self.assertTrue(self.e.match(("i",)))
        self.assertTrue(self.e.match((".",)))
        self.assertTrue(self.e.match(("i*",)))
        self.assertFalse(self.e.match(("j*",)))
        self.assertTrue(self.e.match(("e","i")))
        self.assertTrue(self.e.match(("e",1)))
        self.assertTrue(self.e.match(("e",".")))
        self.assertTrue(self.e.match(("e","i*",)))
        self.assertFalse(self.e.match(("e","j*")))
        self.assertTrue(self.e.match((".","i")))
        self.assertTrue(self.e.match((".",1)))
        self.assertTrue(self.e.match((".",".")))
        self.assertTrue(self.e.match((".","i*",)))
        self.assertFalse(self.e.match((".","j*")))
        self.assertFalse(self.e.match((".","i","j")))
        self.assertFalse(self.e.match((".",".","j")))
        self.assertFalse(self.e.match((".","i*","j")))
        self.assertFalse(self.e.match((".","j*","j")))
        
    def test_discard(self):
        e = ExtensibleTree()
        e.a.a = 1
        e.b.c = []
        e.b.d = {}
        # identifier 
        self.assertTrue("a" in e)
        e.discard("a")
        self.assertFalse("a" in e)
        # path
        self.assertTrue(("b", "c") in e)
        e.discard(("b", "c"))
        self.assertFalse(("b", "c") in e)
        # not present identifier
        e.discard("d")
        # not present path
        e.discard(("d", "c"))

    def test_update(self):
        e = ExtensibleTree()
        e.a.a = 1
        e.b.c = []
        e.b.d = {}
        e.c = ExtensibleTree()
        ee = ExtensibleTree()
        ee.a.a = 2
        ee.b = 3
        ee.update(e)
        self.assertEqualAndSeparated(e, ee)

    def assertEqualAndSeparated(self, e1, e2):
        for k, v in e1.items():
            self.assertIn(k, e2)
            v2 = e2[k]
            if isinstance(v, ExtensibleTree):
                self.assertNotEqual(id(v), id(v2))
                self.assertEqualAndSeparated(v, v2)
            else:
                self.assertEqual(v, v2)

    # ---------------------------------------------------------------------
    #  Emulating container type   

    def test__len__(self):
        self.assertEqual(len(self.e), len(self.dict))

    def test__iter__(self):
        keys = set()
        for k in self.e:
            keys.add(k)
        self.assertEqual(keys, self.dict.keys())

    def test__getitem__(self):
        e = ExtensibleTree()
        e.e11 = ExtensibleTree(self.dict)
        e.e21.i = 1
        e.e22.i = 2
        e.e21[1] = 6
        e.e21[2] = 7
        e.e22[1] = 8
        e[1].i = 3
        # single matching
        self.assertEqual(e["e11"]["i"], self.dict["i"])
        # regexp no result
        self.assertFalse(e["u*"])
        # regexp single result
        res = e[".11"]["i"]
        self.assertEqual(len(res), 1)
        self.assertEqual(list(res), [self.dict["i"]])
        # regexp multiple result
        res = list(e[".2."]["i"])
        self.assertEqual(len(res), 2)
        self.assertIn(1, res)
        self.assertIn(2, res)
        # numeric single result
        self.assertEqual(e["e21"][1], 6)
        # numeric-regexp multiple result 
        res = e["e2."][1]
        self.assertEqual(len(res), 2)
        self.assertIn(6, res)
        self.assertIn(8, res)
        # complete slice at end
        res = e["e22"][:]
        self.assertEqual(len(res), 2)
        self.assertIn(2, res)
        self.assertIn(8, res)
        # complete slice at middle
        res = collections.Counter(e[:]["i"])
        self.assertEqual(res[1], 2)
        self.assertEqual(res[2], 1)
        self.assertEqual(res[3], 1)
        # any different slice raises Exception
        self.assertRaises(ValueError, e.__getitem__, slice(1))
        self.assertRaises(ValueError, e.__getitem__, slice(1, None))
        self.assertRaises(ValueError, e.__getitem__, slice(None, None, 1))
        # private or inexistent attributes
        self.assertRaises(KeyError, e.__getitem__, "update")

    def test__setitem__(self):
        e = ExtensibleTree()
        # single matching
        e["e11"]["i"] = self.dict["i"]
        self.assertEqual(e.e11.i, self.dict["i"])
        # regexp single result
        e[".11"]["i"] = 2
        self.assertEqual(e.e11.i, 2)
        # regexp multiple result
        e["e21"] = None
        e["e22"] = None
        e[".2."] = "set"
        res = list(e[".2."])
        self.assertEqual(res, ["set", "set"])
        # numeric single result
        e["e21"] = ExtensibleTree()
        e["e21"][1] = 6
        self.assertEqual(e["e21"][1], 6)
        # numeric-regexp multiple result 
        e["e22"] = ExtensibleTree()
        e["e2."][1] = 8
        res = list(e["e2."][1])
        self.assertEqual(res, [8,8])
        # complete slice at end
        e["e22"][2] = 9
        e["e22"][:] = 10
        res = list(e["e22"][:])
        self.assertEqual(res, [10,10])
        # complete slice at middle
        e[:][5] = 5
        res = list(e[:][5])
        self.assertEqual(res, [5,5,5])
        # any different slice raises Exception
        self.assertRaises(ValueError, e.__setitem__, slice(1), None)
        self.assertRaises(ValueError, e.__setitem__, slice(1, None), None)
        self.assertRaises(ValueError, e.__setitem__, slice(None, None, 1), None)
        # private attributes
        self.assertRaises(KeyError, e.__setitem__, "update", None)

    def test__delitem__(self):
        #  TODO: add other tests like test__setitem__
        e = ExtensibleTree()
        del self.e["i"]
        self.assertEqual(set(self.e), {1, "t", "l", "d"})
        self.assertRaises(ValueError, e.__delitem__, slice(1))
        self.assertRaises(ValueError, e.__delitem__, slice(1, None))
        self.assertRaises(ValueError, e.__delitem__, slice(None, None, 1))
        # private attributes
        self.assertRaises(KeyError, e.__delitem__, "update")

    def test__contains__(self):
        for p in self.e.paths():
            self.assertTrue(p in self.e)
        self.assertFalse("update" in self.e)
        
# -------------------------------------------------------------------

def suite():
    tests = list(t for t in TestExtensibleTree.__dict__ \
                   if t.startswith("test_"))
    return unittest.TestSuite(list(map(TestExtensibleTree, tests)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
