#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# boing/test/net/test__slip__.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import itertools
import unittest

from boing.net import slip

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

    def test_SingleEncoderDecoder(self):
        data = bytearray(__name__, "utf-8")
        encoder = slip.Encoder()
        decoder = slip.Decoder()
        encoded = encoder.encode(data)
        decoded = decoder.decode(encoded)
        self.assertEqual(len(decoded), 1)
        self.assertEqual(decoded[0], data)

    def test_MultipleEncoderDecoder(self):
        encoder = slip.Encoder()
        decoder = slip.Decoder()
        name = bytes("test_MultipleEncoderDecoder", "utf-8")
        file = bytes("boing/test/net/test_slip.py", "utf-8")
        data = (name, file, name, file)
        encoded = sum(map(encoder.encode, data), b"")
        part1 = encoded[:30]
        part2 = encoded[30:40]
        part3 = encoded[40:]
        decoded = decoder.decode(part1)
        self.assertEqual(len(decoded), 1)
        self.assertEqual(decoded[0], name)
        decoded = decoder.decode(part2)
        self.assertFalse(decoded)
        decoded = decoder.decode(part3)
        self.assertEqual(len(decoded), 3)
        self.assertEqual(decoded[0], file)
        self.assertEqual(decoded[1], name)
        self.assertEqual(decoded[2], file)

# -------------------------------------------------------------------

def suite():
    testcases = (
        TestSlip,
        )
    return unittest.TestSuite(itertools.chain(
            *(map(t, filter(lambda f: f.startswith("test_"), dir(t))) \
                  for t in testcases)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
