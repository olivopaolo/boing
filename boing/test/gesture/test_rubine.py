#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# boing/test/gesture/test_rubine.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import itertools
import unittest
import weakref

from boing.gesture import rubine

class TestRubine(unittest.TestCase):

    def test_isValid(self):
        recognizer = rubine.RubineRecognizer()
        for name, stroke in rubine.testInstances():
            self.assertTrue(recognizer.isValid(stroke))

    def test_loadTestTemplates(self):
        recognizer = rubine.RubineRecognizer()
        recognizer.loadTestTemplates()
        self.assertIsNotNone(recognizer.classes())
        for name, stroke in rubine.testInstances():
            result = recognizer.recognize(rubine.normalize(stroke))
            self.assertEqual(result["cls"], name)

    def test_buildRecognizer(self):
        recognizer = rubine.RubineRecognizer()
        recognizer.buildRecognizer(rubine.testInstances())
        self.assertIsNotNone(recognizer.classes())
        for name, stroke in rubine.testInstances():
            result = recognizer.recognize(rubine.normalize(stroke))
            self.assertEqual(result["cls"], name)

# -------------------------------------------------------------------

def suite():
    testcases = (
        TestRubine,
        )
    return unittest.TestSuite(itertools.chain(
            *(map(t, filter(lambda f: f.startswith("test_"), dir(t))) \
                  for t in testcases)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
