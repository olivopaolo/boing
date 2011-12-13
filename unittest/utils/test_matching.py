#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# test/utils/test_matching.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import unittest

from boing.utils import matching

class TestMatching(unittest.TestCase):

    def test_matchKeys(self):
        self.assertFalse(matching.matchKeys(None, "boing"))
        self.assertTrue(matching.matchKeys("boing", "boing"))
        self.assertTrue(matching.matchKeys(".*", "boing"))
        self.assertTrue(matching.matchKeys("boing", ".*"))
        self.assertFalse(matching.matchKeys(None, ".*"))        
        self.assertTrue(matching.matchKeys(1, 1))
        self.assertTrue(matching.matchKeys(".*", 1))
        self.assertTrue(matching.matchKeys(1, ".*"))
        self.assertTrue(matching.matchKeys(".*", ".*"))
        self.assertTrue(matching.matchKeys("boing", "boi.*"))
        self.assertTrue(matching.matchKeys(".*ing", "boing"))
        self.assertTrue(matching.matchKeys("boi.*", "boi.*"))
        self.assertTrue(matching.matchKeys(".*ing", ".*ing"))
        # TODO: regexp subset should be handled
        self.assertFalse(matching.matchKeys("b.*", "boi.*"))
        self.assertFalse(matching.matchKeys(".*g", ".*ing"))

    def test_matchPaths(self):
        # Both unitary
        self.assertFalse(matching.matchPaths(None, "boing"))
        self.assertTrue(matching.matchPaths("boing", "boing"))
        self.assertTrue(matching.matchPaths(".*", "boing"))
        self.assertTrue(matching.matchPaths("boing", ".*"))
        self.assertFalse(matching.matchPaths(None, ".*"))        
        self.assertTrue(matching.matchPaths(1, 1))
        self.assertTrue(matching.matchPaths(".*", 1))
        self.assertTrue(matching.matchPaths(1, ".*"))
        self.assertTrue(matching.matchPaths(".*", ".*"))
        self.assertTrue(matching.matchPaths("boing", "boi.*"))
        self.assertTrue(matching.matchPaths(".*ing", "boing"))
        self.assertTrue(matching.matchPaths("boi.*", "boi.*"))
        self.assertTrue(matching.matchPaths(".*ing", ".*ing"))
        # TODO: regexp subset should be handled
        self.assertFalse(matching.matchPaths("b.*", "boi.*"))
        self.assertFalse(matching.matchPaths(".*g", ".*ing"))
        # First unitary, second path
        self.assertFalse(matching.matchPaths(None, "boing"))
        self.assertTrue(matching.matchPaths("boing", ("boing", "boing")))
        self.assertTrue(matching.matchPaths(".*",  ("boing", "boing")))
        self.assertTrue(matching.matchPaths("boing", (".*", "boing")))
        self.assertFalse(matching.matchPaths(None, (".*", "boing")))
        self.assertTrue(matching.matchPaths(1, (1, "boing")))
        self.assertTrue(matching.matchPaths(".*", (1, "boing")))
        self.assertTrue(matching.matchPaths(1, (".*", "boing")))
        self.assertTrue(matching.matchPaths(".*", (".*", "boing")))
        self.assertTrue(matching.matchPaths("boing", ("boi.*", "boing")))
        self.assertTrue(matching.matchPaths(".*ing", ("boing", "boing")))
        self.assertTrue(matching.matchPaths("boi.*", ("boi.*","boing")))
        self.assertTrue(matching.matchPaths(".*ing", (".*ing", "boing")))
        # TODO: regexp subset should be handled
        self.assertFalse(matching.matchPaths("b.*", ("boi.*","boing")))
        self.assertFalse(matching.matchPaths(".*g", (".*ing","boing")))
        # First path, second unitary
        self.assertTrue(matching.matchPaths(("boing", "boing"), "boing"))
        self.assertTrue(matching.matchPaths(("boing", "boing"), ".*"))
        self.assertTrue(matching.matchPaths((".*", "boing"), "boing"))
        self.assertFalse(matching.matchPaths((".*", "boing"), None))
        self.assertTrue(matching.matchPaths((1, "boing"), 1))
        self.assertTrue(matching.matchPaths((1, "boing"), ".*"))
        self.assertTrue(matching.matchPaths((".*", "boing"), 1))
        self.assertTrue(matching.matchPaths((".*", "boing"), ".*"))
        self.assertTrue(matching.matchPaths(("boi.*", "boing"), "boing"))
        self.assertTrue(matching.matchPaths(("boing", "boing"), ".*ing"))
        self.assertTrue(matching.matchPaths(("boi.*","boing"), "boi.*"))
        self.assertTrue(matching.matchPaths((".*ing", "boing"), ".*ing"))
        # TODO: regexp subset should be handled
        self.assertFalse(matching.matchPaths(("boi.*","boing"), "b.*"))
        self.assertFalse(matching.matchPaths((".*ing","boing"), ".*g"))
        # Both paths, same size
        self.assertTrue(matching.matchPaths(("boing", "boing"), ("boing","boing")))
        self.assertTrue(matching.matchPaths(("boing", "boing"), (".*","boing")))
        self.assertTrue(matching.matchPaths((".*", "boing"), ("boing","boing")))
        self.assertTrue(matching.matchPaths((1, "boing"), (1,"boing")))
        self.assertTrue(matching.matchPaths((1, "boing"), (".*","boing")))
        self.assertTrue(matching.matchPaths((".*", "boing"), (1,"boing")))
        self.assertTrue(matching.matchPaths((".*", "boing"), (".*","boing")))
        self.assertTrue(matching.matchPaths(("boi.*", "boing"), ("boing","boing")))
        self.assertTrue(matching.matchPaths(("boing", "boing"), (".*ing","boing")))
        self.assertTrue(matching.matchPaths(("boi.*","boing"), ("boi.*","boing")))
        self.assertTrue(matching.matchPaths((".*ing", "boing"), (".*ing","boing")))
        # TODO: regexp subset should be handled
        self.assertFalse(matching.matchPaths(("boi.*","boing"), ("b.*","boing")))
        self.assertFalse(matching.matchPaths((".*ing","boing"), (".*g","boing")))
        # Both paths, one bigger
        self.assertTrue(matching.matchPaths(("boing", "boing"), ("boing",)))
        self.assertTrue(matching.matchPaths(("boing", "boing"), (".*",)))
        self.assertTrue(matching.matchPaths((".*", "boing"), ("boing",)))
        self.assertTrue(matching.matchPaths((1, "boing"), (1,)))
        self.assertTrue(matching.matchPaths((1, "boing"), (".*",)))
        self.assertTrue(matching.matchPaths((".*", "boing"), (1,)))
        self.assertTrue(matching.matchPaths((".*", "boing"), (".*",)))
        self.assertTrue(matching.matchPaths(("boi.*", "boing"), ("boing",)))
        self.assertTrue(matching.matchPaths(("boing", "boing"), (".*ing",)))
        self.assertTrue(matching.matchPaths(("boi.*","boing"), ("boi.*",)))
        self.assertTrue(matching.matchPaths((".*ing", "boing"), (".*ing",)))
        # TODO: regexp subset should be handled
        self.assertFalse(matching.matchPaths(("boi.*","boing"), ("b.*",)))
        self.assertFalse(matching.matchPaths((".*ing","boing"), (".*g",)))
        
# -------------------------------------------------------------------

def suite():
    tests = list(t for t in TestMatching.__dict__ \
                   if t.startswith("test_"))
    return unittest.TestSuite(list(map(TestMatching, tests)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
