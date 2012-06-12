#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# boing/test/nodes/test_logger.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import itertools
import unittest

from boing.nodes.logger import ProductBuffer

class TestProductBuffer(unittest.TestCase):

    def setUp(self):
        self.triggered = False
        self.product = None

    def test_constructor(self):
        buffer = ProductBuffer()
        buffer = ProductBuffer(200, 2)
        buffer = ProductBuffer(changed=lambda: None)
        buffer = ProductBuffer(productDrop=lambda: None)
        # Wrong kwargs
        self.assertRaises(TypeError, ProductBuffer, wrong="wrong")

    def test_sizeLimit(self):
        buffer = ProductBuffer(100)
        self.assertEqual(buffer.sizeLimit(), 100)
        buffer.setSizeLimit(50)
        self.assertEqual(buffer.sizeLimit(), 50)
        # setSizeLimit also removes products if necessary.
        buffer = ProductBuffer(oversizecut=1,
                               productDrop=lambda: setattr(self, "triggered", True))
        buffer.append([self.product]*10)
        buffer.append([self.product]*10)
        buffer.setSizeLimit(10)
        self.assertTrue(self.triggered)
        self.assertEqual(buffer.sum(), 10)
        self.assertEqual(len(buffer), 1)

    def test_append(self):
        buffer = ProductBuffer(changed=lambda: setattr(self, "triggered", True))
        buffer.append([self.product]*10)
        self.assertTrue(self.triggered)

    def test_append_overflow(self):
        buffer = ProductBuffer(10,
                               productDrop=lambda: setattr(self, "triggered", True))
        buffer.append([self.product]*10)
        self.assertFalse(self.triggered)
        buffer.append([self.product]*10)
        self.assertTrue(self.triggered)

    def test_sum(self):
        buffer = ProductBuffer()
        self.assertEqual(buffer.sum(), 0)
        buffer.append([self.product]*10)
        self.assertEqual(buffer.sum(), 10)
        buffer.append([self.product]*10)
        self.assertEqual(buffer.sum(), 20)

    def test_len(self):
        buffer = ProductBuffer()
        self.assertEqual(len(buffer), 0)
        buffer.append([self.product]*10)
        self.assertEqual(len(buffer), 1)
        buffer.append([self.product]*10)
        self.assertEqual(len(buffer), 2)

    def test_clear(self):
        buffer = ProductBuffer()
        buffer.append([self.product]*10)
        self.assertEqual(buffer.sum(), 10)
        self.assertEqual(len(buffer), 1)
        buffer.clear()
        self.assertEqual(buffer.sum(), 0)
        self.assertEqual(len(buffer), 0)

    # FIXME: add index, slice, islice tests

# -------------------------------------------------------------------

def suite():    
    testcases = (
        TestProductBuffer,
        )
    return unittest.TestSuite(itertools.chain(
            *(map(t, filter(lambda f: f.startswith("test_"), dir(t))) \
                  for t in testcases)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
