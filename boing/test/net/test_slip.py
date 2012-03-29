#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# boing/test/net/test__slip__.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import datetime
import io
import unittest

import boing.net.slip as slip

class TestSlip(unittest.TestCase):

    def createMessage(self):
        msg = bytearray()
        msg.extend(b"unittest/slip/test__slip__.py")
        msg.append(slip.END)
        msg.extend(b"unittest/slip/test__slip__.py")
        msg.append(slip.ESC)
        msg.extend(b"unittest/slip/test__slip__.py")
        msg.append(slip.END)
        msg.append(slip.ESC)
        msg.extend(b"unittest/slip/test__slip__.py")
        msg.append(slip.ESC)
        msg.append(slip.END)
        msg.extend(b"unittest/slip/test__slip__.py")
        msg.append(slip.END)
        return msg

    def test_SingleEncodeDecode(self):
        device = bytearray()
        device.extend(slip.encode(self.createMessage()))
        rest = slip.encode(self.createMessage())
        rest = rest[:10]
        device.extend(rest)
        rest = rest[1:] # remove first END
        decoded, stillencoded = slip.decode(device)
        self.assertEqual(len(decoded), 1)
        self.assertEqual(decoded[0], self.createMessage())
        self.assertEqual(stillencoded, rest)

    def test_MultipleEncodeDecode(self):
        device = bytearray()
        device.extend(slip.encode(self.createMessage()))
        device.extend(slip.encode(self.createMessage()))
        device.extend(slip.encode(self.createMessage()))
        rest = slip.encode(self.createMessage())
        rest = rest[:10]
        device.extend(rest)
        rest = rest[1:] # remove first END
        decoded, stillencoded = slip.decode(device)
        self.assertEqual(len(decoded), 3)
        for msg in decoded:            
            self.assertEqual(msg, self.createMessage())
        self.assertEqual(stillencoded, rest)

# -------------------------------------------------------------------

def suite():
    tests = list(t for t in TestSlip.__dict__ \
                     if t.startswith("test_"))
    return unittest.TestSuite(map(TestSlip, tests))    

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
