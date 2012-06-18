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

import boing.net.json as json

class TestJson(unittest.TestCase):

    def test_encode_decode(self):
        obj = {"timetag": datetime.datetime.now(), "data": b"unittest"}
        encoded = json.encode(obj)
        decoded = json.decode(encoded)
        self.assertEqual(obj, decoded)

    def test_SingleEncoderDecoder(self):
        obj = {"timetag": datetime.datetime.now(), "data": b"unittest"}
        encoder = json.Encoder()
        decoder = json.Decoder()
        encoded = encoder.encode(obj)
        decoded = decoder.decode(encoded)
        self.assertEqual(len(decoded), 1)
        self.assertEqual(decoded[0], obj)

# -------------------------------------------------------------------


def suite():
    testcases = (
        TestJson,
        )
    return unittest.TestSuite(itertools.chain(
            *(map(t, filter(lambda f: f.startswith("test_"), dir(t))) \
                  for t in testcases)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
