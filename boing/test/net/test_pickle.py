#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# boing/test/net/test_pickle.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import datetime
import itertools
import unittest

from boing.net import pickle
from boing.utils import quickdict

class CustomClass:
    def __eq__(self, other): return isinstance(other, CustomClass)

class TestPickle(unittest.TestCase):

    def test_encode_decode(self):
        obj = quickdict(a=CustomClass(),
                        timetag=datetime.datetime.now(),
                        data=b"unittest")
        encoded = pickle.encode(obj)
        decoded = pickle.decode(encoded)
        self.assertEqual(obj, decoded)

    def test_SingleEncoderDecoder(self):
        obj = {"a": CustomClass(),
               "timetag": datetime.datetime.now(),
               "data": b"unittest"}
        encoder = pickle.Encoder()
        decoder = pickle.Decoder()
        encoded = encoder.encode(obj)
        decoded = decoder.decode(encoded)
        self.assertEqual(len(decoded), 1)
        self.assertEqual(decoded[0], obj)

# -------------------------------------------------------------------

def suite():
    testcases = (
        TestPickle,
        )
    return unittest.TestSuite(itertools.chain(
            *(map(t, filter(lambda f: f.startswith("test_"), dir(t))) \
                  for t in testcases)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
