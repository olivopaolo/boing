#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# unittest/json_/test__init__.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import datetime
import json
import unittest

import boing.json
from boing.utils.ExtensibleTree import ExtensibleTree

class Test__init__(unittest.TestCase):

    def test_encode_decode(self):
        e = ExtensibleTree()
        e[1] = 1
        e.i = 1
        e.s = "str"
        e.a = [1,2,3]
        e.d = {'1':1, '2':2}
        e.t.s = "inner"
        e.timetag = datetime.datetime.now()
        # ---
        encoded = json.dumps(e, cls=boing.json.ProductEncoder)
        decoded = json.loads(encoded, object_hook=boing.json.productHook)
        # ---
        self.assertEqual(e, decoded)

# -------------------------------------------------------------------

def suite():
    tests = list(t for t in Test__init__.__dict__ \
                     if t.startswith("test_"))
    return unittest.TestSuite(map(Test__init__, tests))    

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
