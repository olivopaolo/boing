#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# unittest/osc/test_LogPlayer.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import io
import os.path
import unittest

from boing import osc
from boing.eventloop.EventLoop import EventLoop
from boing.eventloop.ProducerConsumer import Consumer
from boing.osc.LogPlayer import LogPlayer
from boing.utils.File import File

class TestLogPlayer(unittest.TestCase):

    class DebugConsumer(Consumer):
        
        def __init__(self):
            Consumer.__init__(self)
            self.store = []

        def _consume(self, products, producer):
            self.store.extend(products)

    def setUp(self):
        self.timeout = False

    def timeoutEvent(self, *args, **kwargs):
        self.timeout = True
        EventLoop.stop()

    def getTestLog(self):
        dirname = os.path.dirname(__file__)
        filepath = os.path.abspath(os.path.join(dirname, "..", 
                                               "data", "osclog.osc.bz2"))
        return File(filepath, uncompress=True)

    def test_SinglePlay(self):
        log = self.getTestLog()
        player = LogPlayer(log)
        consumer = TestLogPlayer.DebugConsumer()
        consumer.subscribeTo(player)
        player.stopped.connect(EventLoop.stop)
        player.start(looping=False)
        tid = EventLoop.after(10, self.timeoutEvent)
        EventLoop.run()
        self.assertFalse(self.timeout)
        for p in consumer.store:
            packet = p.osc
            self.assertIsInstance(packet, osc.Packet)
            """data = p.data
            packet_debug = io.StringIO()
            packet.debug(packet_debug)
            data_debug = io.StringIO()
            osc.decode(data).debug(data_debug)
            self.assertEqual(packet_debug.getvalue(), data_debug.getvalue())
            self.assertEqual(packet.encode(), data)"""


# -------------------------------------------------------------------

def suite():
    tests = list(t for t in TestLogPlayer.__dict__ \
                     if t.startswith("test_"))
    return unittest.TestSuite(map(TestLogPlayer, tests))    

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
