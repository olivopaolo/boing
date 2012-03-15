#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# unittest/net/test_json.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import datetime
import json
import unittest

import boing.net.json

class Test__init__(unittest.TestCase):

    def test_encode_decode(self):
        obj = {"timetag": datetime.datetime.now(), "data": b"unittest"}
        encoded = json.dumps(obj, cls=boing.net.json.ProductEncoder)
        decoded = json.loads(encoded, object_hook=boing.net.json.productHook)
        self.assertEqual(obj, decoded)

# -------------------------------------------------------------------

def suite():
    tests = (t for t in Test__init__.__dict__ if t.startswith("test_"))
    return unittest.TestSuite(map(Test__init__, tests))    

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
