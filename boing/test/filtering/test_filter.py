#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# boing/test/filtering/test_filter.py -
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
import weakref

from boing.filtering.filter import \
    createFilter, \
    MovingMeanFilter, MovingMedianFilter, \
    SingleExponentialFilter, DoubleExponentialFilter, DESPFilter, \
    OneEuroFilter

class TestMovingWindowFilter(unittest.TestCase):

    def test_MovingMeanFilter(self):
        # Valid
        for uri in ("fltr:/moving/mean?winsize=5",
                    "/moving/mean?winsize=5",
                    "fltr:/moving/average?winsize=5",
                    "/moving/average?winsize=5",
                    ):
            filt = createFilter(uri)
            self.assertEqual(filt.getURL(), "fltr:/moving/mean?winsize=5")
            self.assertIsNotNone(filt(0.0))
            self.assertIsNotNone(filt(0.0, datetime.datetime.now()))
        for uri in MovingMeanFilter.generateConfigurations(20, 5):
            filt = createFilter(uri)
            self.assertEqual(filt.getURL(), uri)
            self.assertIsNotNone(filt(0.0))
            self.assertIsNotNone(filt(0.0, datetime.datetime.now()))
        uri = MovingMeanFilter.randomConfiguration(50)
        filt = createFilter(uri)
        self.assertEqual(filt.getURL(), uri)
        self.assertIsNotNone(filt(0.0))
        self.assertIsNotNone(filt(0.0, datetime.datetime.now()))
        # Invalid: winsize kwarg is required
        for uri in ("fltr:/moving/mean",
                    "/moving/mean",
                    "fltr:/moving/average",
                    "/moving/average",
                    ):
            self.assertRaises(TypeError, createFilter, uri)
        # Invalid: winsize > 0
        for uri in ("fltr:/moving/mean?winsize=0",
                    "/moving/mean?winsize=0",
                    "fltr:/moving/average?winsize=0",
                    "/moving/average?winsize=0",
                    ):
            self.assertRaises(ValueError, createFilter, uri)

    def test_MovingMedianFilter(self):
        # Valid
        for uri in ("fltr:/moving/median?winsize=5",
                    "/moving/median?winsize=5"):
            filt = createFilter(uri)
            self.assertEqual(filt.getURL(), "fltr:/moving/median?winsize=5")
            self.assertIsNotNone(filt(0.0))
            self.assertIsNotNone(filt(0.0, datetime.datetime.now()))
        for uri in MovingMedianFilter.generateConfigurations(20, 5):
            filt = createFilter(uri)
            self.assertEqual(filt.getURL(), uri)
            self.assertIsNotNone(filt(0.0))
            self.assertIsNotNone(filt(0.0, datetime.datetime.now()))
        uri = MovingMedianFilter.randomConfiguration(50)
        filt = createFilter(uri)
        self.assertEqual(filt.getURL(), uri)
        self.assertIsNotNone(filt(0.0))
        self.assertIsNotNone(filt(0.0, datetime.datetime.now()))
        # Invalid: winsize kwarg is required
        for uri in ("fltr:/moving/median",
                    "/moving/median",
                    ):
            self.assertRaises(TypeError, createFilter, uri)
        # Invalid: winsize > 0
        for uri in ("fltr:/moving/median?winsize=0",
                    "/moving/median?winsize=0",
                    ):
            self.assertRaises(ValueError, createFilter, uri)

class TestExponentialFilter(unittest.TestCase):

    def test_SingleExponentialFilter(self):
        # Valid
        for uri in ("fltr:/exponential/single?alpha=1",
                    "/exponential/single?alpha=1",
                    "/exponential/single?alpha=1&variant=predict",
                    "/exponential/single?alpha=1&variant=lowpass",
                    ):
            filt = createFilter(uri)
            self.assertEqual(filt.getURL(), "fltr:/exponential/single?alpha=1.0")
            self.assertIsNotNone(filt(0.0))
            self.assertIsNotNone(filt(0.0, datetime.datetime.now()))
        for uri in SingleExponentialFilter.generateConfigurations(5):
            filt = createFilter(uri)
            self.assertEqual(filt.getURL(), uri)
            self.assertIsNotNone(filt(0.0))
            self.assertIsNotNone(filt(0.0, datetime.datetime.now()))
        uri = SingleExponentialFilter.randomConfiguration()
        filt = createFilter(uri)
        self.assertEqual(filt.getURL(), uri)
        self.assertIsNotNone(filt(0.0))
        self.assertIsNotNone(filt(0.0, datetime.datetime.now()))
        # Invalid: alpha kwarg is required
        for uri in ("fltr:/exponential/single",
                    "/exponential/single",
                    "fltr:/exponential/single?variant=predict",
                    "/exponential/single?variant=predict",
                    ):
            self.assertRaises(TypeError, createFilter, uri)
        # Invalid: variant not in ('predict', 'lowpass')
        for uri in ("fltr:/exponential/single?varian=wrong",
                    "/exponential/single?varian=wrong",
                    ):
            self.assertRaises(TypeError, createFilter, uri)
        # Invalid: 0 < alpha <= 1
        for uri in ("fltr:/exponential/single?alpha=0",
                    "/exponential/single?alpha=0",
                    "fltr:/exponential/single?alpha=1.1",
                    "/exponential/single?alpha=1.1"
                    ):
            self.assertRaises(ValueError, createFilter, uri)

    def test_DoubleExponentialFilter(self):
        # Valid
        for uri in ("fltr:/exponential/double?alpha=1&gamma=1",
                    "/exponential/double?alpha=1&gamma=1",
                    ):
            filt = createFilter(uri)
            self.assertEqual(filt.getURL(),
                             "fltr:/exponential/double?alpha=1.0&gamma=1.0")
            self.assertIsNotNone(filt(0.0))
            self.assertIsNotNone(filt(0.0, datetime.datetime.now()))
        for uri in DoubleExponentialFilter.generateConfigurations(5):
            filt = createFilter(uri)
            self.assertEqual(filt.getURL(), uri)
            self.assertIsNotNone(filt(0.0))
            self.assertIsNotNone(filt(0.0, datetime.datetime.now()))
        uri = DoubleExponentialFilter.randomConfiguration()
        filt = createFilter(uri)
        self.assertEqual(filt.getURL(), uri)
        self.assertIsNotNone(filt(0.0))
        self.assertIsNotNone(filt(0.0, datetime.datetime.now()))
        # Invalid: alpha kwarg is required
        for uri in ("fltr:/exponential/double?gamma=1",
                    "/exponential/double?gamma=1",
                    ):
            self.assertRaises(TypeError, createFilter, uri)
        # Invalid: gamma kwarg is required
        for uri in ("fltr:/exponential/double?alpha=1",
                    "/exponential/double?alpha=1",
                    ):
            self.assertRaises(TypeError, createFilter, uri)
        # Invalid: 0 <= alpha <= 1
        for uri in ("fltr:/exponential/double?alpha=-0.1&gamma=1",
                    "/exponential/double?alpha=-0.1&gamma=1",
                    "fltr:/exponential/double?alpha=1.1&gamma=1",
                    "/exponential/double?alpha=1.1&gamma=1"
                    ):
            self.assertRaises(ValueError, createFilter, uri)
        # Invalid: 0 <= gamma <= 1
        for uri in ("fltr:/exponential/double?alpha=0&gamma=-0.1",
                    "/exponential/double?alpha=0&gamma=-0.1",
                    "fltr:/exponential/double?alpha=0&gamma=1.1",
                    "/exponential/double?alpha=0&gamma=1.1"
                    ):
            self.assertRaises(ValueError, createFilter, uri)

    def test_DESPFilter(self):
        # Valid
        for uri in ("fltr:/exponential/desp?alpha=0",
                    "/exponential/desp?alpha=0",
                    "fltr:/exponential/desp?alpha=0&tau=1",
                    "/exponential/desp?alpha=0&tau=1",
                    ):
            filt = createFilter(uri)
            self.assertEqual(filt.getURL(),
                             "fltr:/exponential/desp?alpha=0&tau=1")
            self.assertIsNotNone(filt(0.0))
            self.assertIsNotNone(filt(0.0, datetime.datetime.now()))
        for uri in DESPFilter.generateConfigurations(5):
            filt = createFilter(uri)
            self.assertEqual(filt.getURL(), uri)
            self.assertIsNotNone(filt(0.0))
            self.assertIsNotNone(filt(0.0, datetime.datetime.now()))
        uri = DESPFilter.randomConfiguration()
        filt = createFilter(uri)
        self.assertEqual(filt.getURL(), uri)
        self.assertIsNotNone(filt(0.0))
        self.assertIsNotNone(filt(0.0, datetime.datetime.now()))
        # Invalid: alpha kwarg is required
        for uri in ("fltr:/exponential/desp?tau=1",
                    "/exponential/desp?tau=1",
                    ):
            self.assertRaises(TypeError, createFilter, uri)
        # Invalid: 0 <= alpha < 1
        for uri in ("fltr:/exponential/desp?alpha=1",
                    "/exponential/desp?alpha=1",
                    ):
            self.assertRaises(ValueError, createFilter, uri)
        # Invalid: tau > 0
        for uri in ("fltr:/exponential/desp?alpha=0&tau=0",
                    "/exponential/desp?alpha=0&tau=0",
                    ):
            self.assertRaises(ValueError, createFilter, uri)


class TestKalmanFilter(unittest.TestCase):

    def test_ConstantValueKalmanFilter(self):
        # Valid
        for uri in ("fltr:/kalman/constant",
                    "/kalman/constant",
                    "/kalman/constant?x=None",
                    "/kalman/constant?p=1.0",
                    "/kalman/constant?q=1e-05",
                    "/kalman/constant?r=0.1",
                    ):
            filt = createFilter(uri)
            self.assertEqual(
                filt.getURL(),
                "fltr:/kalman/constant?x=None&p=1.0&q=1e-05&r=0.1")
            self.assertIsNotNone(filt(0.0))
            self.assertIsNotNone(filt(0.0, datetime.datetime.now()))

    def test_DerivativeBasedKalmanFilter(self):
        # Valid
        for uri in ("fltr:/kalman/derivative",
                    "/kalman/derivative",
                    "/kalman/derivative?x=0.0",
                    "/kalman/derivative?v=0.0",
                    "/kalman/derivative?freq=60",
                    "/kalman/derivative?p=1.0",
                    "/kalman/derivative?q=1e-05",
                    "/kalman/derivative?r=0.1",
                    ):
            filt = createFilter(uri)
            self.assertEqual(
                filt.getURL(),
                "fltr:/kalman/derivative?x=0.0&v=0.0&freq=60&p=1.0&q=1e-05&r=0.1")
            self.assertIsNotNone(filt(0.0))
            self.assertIsNotNone(filt(0.0, datetime.datetime.now()))


class TestOneEuroFilter(unittest.TestCase):

    def test_OneEuroFilter(self):
        # Valid
        for uri in ("fltr:/oneeuro?freq=1",
                    "/oneeuro?freq=1",
                    ):
            filt = createFilter(uri)
            self.assertEqual(
                filt.getURL(),
                "fltr:/oneeuro?freq=1&mincutoff=1&beta=0&dcutoff=1")
            self.assertIsNotNone(filt(0.0))
            self.assertIsNotNone(filt(0.0, datetime.datetime.now()))
        for uri in OneEuroFilter.generateConfigurations(1.0, 1.0, 10, 0.5, 10):
            filt = createFilter(uri)
            self.assertEqual(filt.getURL(), uri)
            self.assertIsNotNone(filt(0.0))
            self.assertIsNotNone(filt(0.0, datetime.datetime.now()))
        uri = OneEuroFilter.randomConfiguration(120)
        filt = createFilter(uri)
        self.assertEqual(filt.getURL(), uri)
        self.assertIsNotNone(filt(0.0))
        self.assertIsNotNone(filt(0.0, datetime.datetime.now()))
        # Invalid: freq kwarg is required
        for uri in ("fltr:oneeuro",
                    "oneeuro",
                    ):
            self.assertRaises(TypeError, createFilter, uri)
        # Invalid: freq > 0
        for uri in ("fltr:/oneeuro?freq=0",
                    "/oneeuro?freq=0",
                    ):
            self.assertRaises(ValueError, createFilter, uri)


# -------------------------------------------------------------------

def suite():
    testcases = (
        TestMovingWindowFilter,
        TestExponentialFilter,
        TestKalmanFilter,
        TestOneEuroFilter,
        )
    return unittest.TestSuite(itertools.chain(
            *(map(t, filter(lambda f: f.startswith("test_"), dir(t))) \
                  for t in testcases)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
