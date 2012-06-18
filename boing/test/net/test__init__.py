#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# boing/test/net/test_json.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import datetime
import itertools
import unittest

from boing.net import bytes, json, slip

class Test_CompositeDecoder(unittest.TestCase):

    def test_SingleJsonBytesSlip(self):
        obj = {"timetag": datetime.datetime.now(), "data": b"unittest"}
        jsonencoder = json.Encoder()
        bytesencoder = bytes.Encoder()
        slipencoder = slip.Encoder()
        encoded = slipencoder.encode(bytesencoder.encode(jsonencoder.encode(obj)))
        decoder = slip.Decoder() + bytes.Decoder() + json.Decoder()
        decoded = decoder.decode(encoded)
        self.assertEqual(len(decoded), 1)
        self.assertEqual(decoded[0], obj)

    def test_MultipleJsonBytesSlip(self):
        obj1 = {"timetag": datetime.datetime.now(), "data": b"unittest"}
        obj2 = [datetime.datetime.now(), b"unittest"]
        obj3 = {"dict": obj1, "list": obj2}
        objs = (obj1, obj2, obj3)
        jsonencoder = json.Encoder()
        bytesencoder = bytes.Encoder()
        slipencoder = slip.Encoder()
        l = lambda obj: \
            slipencoder.encode(bytesencoder.encode(jsonencoder.encode(obj)))
        encoded = sum(map(l, objs), b"")
        decoder = slip.Decoder() + bytes.Decoder() + json.Decoder()
        part1 = encoded[:90]
        part2 = encoded[90:120]
        part3 = encoded[120:]
        decoded = decoder.decode(part1)
        self.assertEqual(len(decoded), 1)
        self.assertEqual(decoded[0], obj1)
        decoded = decoder.decode(part2)
        self.assertFalse(decoded)
        decoded = decoder.decode(part3)
        self.assertEqual(len(decoded), 2)
        self.assertEqual(decoded[0], obj2)
        self.assertEqual(decoded[1], obj3)

# -------------------------------------------------------------------


def suite():
    testcases = (
        Test_CompositeDecoder,
        )
    return unittest.TestSuite(itertools.chain(
            *(map(t, filter(lambda f: f.startswith("test_"), dir(t))) \
                  for t in testcases)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
