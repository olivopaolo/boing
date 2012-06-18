#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# boing/test/utils/test__init__.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import itertools
import unittest

from boing.utils import assertIsInstance

class Test_assertIsInstance(unittest.TestCase):

    def setUp(self):
        self.classes = set([None, bool, int, float, str, tuple, list, dict, set])

    def test_single(self):
        for testclass in self.classes:
            obj = None if testclass is None else testclass()
            assertIsInstance(obj, testclass)
            assertIsInstance(obj, None if obj is None else type(obj))

    def test_multiple(self):
        for testclass in self.classes:
            obj = None if testclass is None else testclass()
            assertIsInstance(obj, *self.classes)
        assertIsInstance(None, None, int)

    def test_raises(self):
        for testclass in self.classes:
            obj = None if testclass is None else testclass()
            # Since boolean is also integers
            complement = self.classes - {int, bool} if testclass is bool \
                else self.classes-{testclass}
            self.assertRaises(TypeError, assertIsInstance, obj, *complement)


# -------------------------------------------------------------------

def suite():
    testcases = (
        Test_assertIsInstance,
        )
    return unittest.TestSuite(itertools.chain(
            *(map(t, filter(lambda f: f.startswith("test_"), dir(t))) \
                  for t in testcases)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())

