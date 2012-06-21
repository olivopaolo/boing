#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# boing/test/net/test_osc.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import datetime
import io
import itertools
import unittest

import boing.net.osc as osc

class TestClasses(unittest.TestCase):

    def setUp(self):
        self.address = "/test"

    def test_Message_empty(self):
        self.assertRaises(TypeError, osc.Message, None)

    def test_Message_address(self):
        msg1 = osc.Message(self.address)
        debug1 = io.StringIO()
        msg1.debug(debug1)
        data1 = msg1.encode()
        msg2 = osc.decode(data1)
        debug2 = io.StringIO()
        msg2.debug(debug2)
        data2 = msg2.encode()
        self.assertEqual(msg1.address, self.address)
        self.assertEqual(msg2.address, self.address)
        self.assertEqual(msg1.typetags, "")
        self.assertEqual(msg2.typetags, "")
        self.assertFalse(msg1.arguments)
        self.assertFalse(msg2.arguments)
        self.assertIsInstance(str(msg1), str)
        self.assertIsInstance(str(msg2), str)
        self.assertEqual(data1, data2)
        self.assertEqual(debug1.getvalue(), debug2.getvalue())

    def test_Message_arguments(self):
        msg1 = osc.Message(self.address,"iifs",17,10,0.125,"unittest")
        debug1 = io.StringIO()
        msg1.debug(debug1)
        data1 = msg1.encode()
        msg2 = osc.decode(data1)
        debug2 = io.StringIO()
        msg2.debug(debug2)
        data2 = msg2.encode()
        self.assertEqual(msg1.address, self.address)
        self.assertEqual(msg2.address, self.address)
        self.assertEqual(msg1.typetags, "iifs")
        self.assertEqual(msg2.typetags, "iifs")
        self.assertEqual(msg1.arguments, (17,10,0.125,"unittest"))
        self.assertEqual(msg2.arguments, (17,10,0.125,"unittest"))
        self.assertIsInstance(str(msg1), str)
        self.assertIsInstance(str(msg2), str)
        self.assertEqual(data1, data2)
        self.assertEqual(debug1.getvalue(), debug2.getvalue())

    def test_Message_bad_typetag(self):
        msg = osc.Message(self.address,"",17)
        self.assertRaises(TypeError, msg.encode)
        msg = osc.Message(self.address,"ss",17)
        self.assertRaises(TypeError, msg.encode)

    def test_Message_not_arguments_typetag(self):
        msg1 = osc.Message(self.address,"TFNIi",17)
        debug1 = io.StringIO()
        msg1.debug(debug1)
        data1 = msg1.encode()
        msg2 = osc.decode(data1)
        debug2 = io.StringIO()
        msg2.debug(debug2)
        data2 = msg2.encode()
        self.assertEqual(msg1.address, self.address)
        self.assertEqual(msg2.address, self.address)
        self.assertEqual(msg1.typetags, "TFNIi")
        self.assertEqual(msg2.typetags, "TFNIi")
        self.assertEqual(msg1.arguments, (17,))
        self.assertEqual(msg2.arguments, (17,))
        self.assertIsInstance(str(msg1), str)
        self.assertIsInstance(str(msg2), str)
        self.assertEqual(data1, data2)
        self.assertEqual(debug1.getvalue(), debug2.getvalue())

    def test_Message_None_typetag(self):
        msg1 = osc.Message(self.address,None,17,0.125,"unittest")
        debug1 = io.StringIO()
        msg1.debug(debug1)
        data1 = msg1.encode()
        msg2 = osc.decode(data1)
        debug2 = io.StringIO()
        msg2.debug(debug2)
        data2 = msg2.encode()
        self.assertEqual(msg1.address, self.address)
        self.assertEqual(msg2.address, self.address)
        self.assertIsNone(msg1.typetags)
        self.assertEqual(msg2.typetags, "ifs")
        self.assertEqual(msg1.arguments, (17,0.125,"unittest"))
        self.assertEqual(msg2.arguments, (17,0.125,"unittest"))
        self.assertIsInstance(str(msg1), str)
        self.assertIsInstance(str(msg2), str)
        self.assertEqual(data1, data2)
        self.assertIsNotNone(debug1.getvalue())
        self.assertIsNotNone(debug2.getvalue())
        self.assertEqual(msg1.address, msg2.address)
        self.assertEqual(msg1.arguments, msg2.arguments)

    def test_Message_bytes_argument(self):
        msg1 = osc.Message(self.address,None, b"unittest")
        debug1 = io.StringIO()
        msg1.debug(debug1)
        data1 = msg1.encode()
        msg2 = osc.decode(data1)
        debug2 = io.StringIO()
        msg2.debug(debug2)
        data2 = msg2.encode()
        self.assertEqual(msg1.address, self.address)
        self.assertEqual(msg2.address, self.address)
        self.assertIsInstance(str(msg1), str)
        self.assertIsInstance(str(msg2), str)
        self.assertEqual(data1, data2)
        self.assertIsNotNone(debug1.getvalue())
        self.assertIsNotNone(debug2.getvalue())
        self.assertEqual(msg1.address, msg2.address)
        self.assertEqual(msg1.arguments, msg2.arguments)

    def test_Message_bytes_no_typetag(self):
        msg1 = osc.Message(self.address,"b",b"unittest")
        debug1 = io.StringIO()
        msg1.debug(debug1)
        data1 = msg1.encode()
        msg2 = osc.decode(data1)
        debug2 = io.StringIO()
        msg2.debug(debug2)
        data2 = msg2.encode()
        self.assertEqual(msg1.address, self.address)
        self.assertEqual(msg2.address, self.address)
        self.assertEqual(msg1.typetags, "b")
        self.assertEqual(msg2.typetags, "b")
        self.assertEqual(msg1.arguments, (b"unittest",))
        self.assertEqual(msg2.arguments, (b"unittest",))      
        self.assertIsInstance(str(msg1), str)
        self.assertIsInstance(str(msg2), str)
        self.assertEqual(data1, data2)
        self.assertEqual(debug1.getvalue(), debug2.getvalue())

    def test_Bundle(self):
        timetag = datetime.datetime.now()
        bdl1 = osc.Bundle(timetag,
                          (osc.Message(self.address,"is",1,"unittest"), 
                           osc.Message(self.address,"TFNIib",2,b"unittest")))
        debug1 = io.StringIO()
        bdl1.debug(debug1)
        data1 = bdl1.encode()
        bdl2 = osc.decode(data1)
        debug2 = io.StringIO()
        bdl2.debug(debug2)
        data2 = bdl2.encode()
        self.assertEqual(bdl1.timetag, timetag)
        self.assertEqual(bdl2.timetag, timetag)
        self.assertIsInstance(str(bdl1), str)
        self.assertIsInstance(str(bdl2), str)
        self.assertEqual(data1, data2)
        self.assertEqual(debug1.getvalue(), debug2.getvalue())

    def test_nested_Bundle(self):
        timetag = datetime.datetime.now()
        bdl1 = osc.Bundle(timetag,
                          (osc.Bundle(None, 
                                      (osc.Message(self.address,"i",1),
                                       osc.Message(self.address,"i",2))), 
                           osc.Message(self.address,"f",2.0)))
        debug1 = io.StringIO()
        bdl1.debug(debug1)
        data1 = bdl1.encode()
        bdl2 = osc.decode(data1)
        debug2 = io.StringIO()
        bdl2.debug(debug2)
        data2 = bdl2.encode()
        self.assertEqual(bdl1.timetag, timetag)
        self.assertEqual(bdl2.timetag, timetag)
        self.assertIsInstance(str(bdl1), str)
        self.assertIsInstance(str(bdl2), str)
        self.assertEqual(data1, data2)
        self.assertEqual(debug1.getvalue(), debug2.getvalue())

    def test_Bundle_source(self):
        timetag = datetime.datetime.now()
        source = "test_osc.py"
        bdl1 = osc.Bundle(timetag,
                          (osc.Message(self.address,"is",1,"unittest"),
                           osc.Message(self.address,"TFNIib",2,b"unittest")))
        bdl1.source = source
        debug1 = io.StringIO()
        bdl1.debug(debug1)
        data1 = bdl1.encode()
        bdl2 = osc.decode(data1)
        debug2 = io.StringIO()
        bdl2.debug(debug2)
        data2 = bdl2.encode()
        self.assertEqual(bdl1.timetag, timetag)
        self.assertEqual(bdl2.timetag, timetag)
        self.assertEqual(bdl1.source, source)
        self.assertNotEqual(bdl2.source, source)
        self.assertIsInstance(str(bdl1), str)
        self.assertIsInstance(str(bdl2), str)
        self.assertEqual(data1, data2)
        self.assertEqual(debug1.getvalue(), debug2.getvalue())

class TestEncoder(unittest.TestCase):

    def test_SingleEncoderDecoder(self):
        bdl = osc.Bundle(datetime.datetime.now(),
                         (osc.Message("/test", "is", 1, "unittest"),
                          osc.Message("/test/boing", "TFNIib", 2, b"unittest")))
        encoder = osc.Encoder()
        decoder = osc.Decoder()
        encoded = encoder.encode(bdl)
        decoded = decoder.decode(encoded)
        self.assertEqual(len(decoded), 1)
        stream = io.StringIO()
        bdl.debug(stream)
        decoded[0].debug(stream)
        text = stream.getvalue()
        self.assertEqual(text[:int(len(text)/2)], text[int(len(text)/2):])

# -------------------------------------------------------------------

def suite():
    testcases = (
        TestClasses,
        TestEncoder,
        )
    return unittest.TestSuite(itertools.chain(
            *(map(t, filter(lambda f: f.startswith("test_"), dir(t))) \
                  for t in testcases)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
