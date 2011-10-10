#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# unittest/display/test_DisplayDevice.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import sys
import unittest

from boing.display.DisplayDevice import DisplayDevice, Size, Point, Bounds
from boing.url import URL

class CreateCase(unittest.TestCase): 
   
    def test_empty(self):
        d = DisplayDevice.create()
        self.assertIsInstance(d, DisplayDevice)
        if sys.platform=="linux2":
            self.assertEqual(d.url.scheme, "xorgdisplay")
        elif sys.platform=="win32":
            self.assertEqual(d.url.scheme, "windisplay")
        else:
            self.assertEqual(d.url.scheme, "dummy")
        self.assertIsInstance(d.bounds, Bounds)
        self.assertIsInstance(d.size, Size)
        self.assertIsInstance(d.resolution[0], float)
        self.assertIsInstance(d.resolution[1], float)
        self.assertIsInstance(d.refreshrate, float)
        self.assertIsInstance(d.url, URL)

    def test_None(self):
        d = DisplayDevice.create(None)
        self.assertIsInstance(d, DisplayDevice)
        if sys.platform=="linux2":
            self.assertEqual(d.url.scheme, "xorgdisplay")
        elif sys.platform=="win32":
            self.assertEqual(d.url.scheme, "windisplay")
        else:
            self.assertEqual(d.url.scheme, "dummy")
        self.assertIsInstance(d.resolution[0], float)
        self.assertIsInstance(d.resolution[1], float)
        self.assertIsInstance(d.refreshrate, float)
        self.assertIsInstance(d.url, URL)

    def test_any(self):
        d = DisplayDevice.create("any:")
        if sys.platform=="linux2":
            self.assertEqual(d.url.scheme, "xorgdisplay")
        elif sys.platform=="win32":
            self.assertEqual(d.url.scheme, "windisplay")
        else:
            self.assertEqual(d.url.scheme, "dummy")
        self.assertIsInstance(d.bounds, Bounds)
        self.assertIsInstance(d.size, Size)
        self.assertIsInstance(d.resolution[0], float)
        self.assertIsInstance(d.resolution[1], float)
        self.assertIsInstance(d.refreshrate, float)
        self.assertIsInstance(d.url, URL)

    def test_dummy(self):
        d = DisplayDevice.create("dummy:")
        self.assertEqual(d.bounds, Bounds(0,0,0,0))
        self.assertEqual(d.size, Size(0,0))
        self.assertIsInstance(d.resolution[0], float)
        self.assertIsInstance(d.resolution[1], float)
        self.assertIsInstance(d.refreshrate, float)
        self.assertEqual(d.url.scheme, "dummy")
        
        
    def test_dummy_arguments(self):
        d = DisplayDevice.create("dummy:?w=300&h=400&bx=50&by=75&bw=100&bh=200&ppi=500&hz=800")
        self.assertEqual(d.bounds, Bounds(50,75,100,200))
        self.assertEqual(d.size, Size(300,400))
        self.assertEqual(d.resolution, (500.0,500.0))
        self.assertEqual(d.refreshrate, 800)
        url = d.url
        self.assertEqual(int(url.query.data['bx']), 50)
        self.assertEqual(int(url.query.data['by']), 75)
        self.assertEqual(int(url.query.data['bw']), 100)
        self.assertEqual(int(url.query.data['bh']), 200)
        self.assertEqual(int(url.query.data['w']), 300)
        self.assertEqual(int(url.query.data['h']), 400)
        self.assertEqual(int(url.query.data['ppi']), 500)        
        self.assertEqual(int(url.query.data['hz']), 800)       

    def test_dummy_setters(self):
        d = DisplayDevice.create("dummy:")
        d.setBounds(Bounds(50,75,100,200))
        d.setSize(Size(300,400))
        d.setResolution(500)
        d.setRefreshRate(800)
        self.assertEqual(d.bounds, Bounds(50,75,100,200))
        self.assertEqual(d.size, Size(300,400))
        self.assertEqual(d.resolution, (500.0,500.0))
        self.assertEqual(d.refreshrate, 800)
        url = d.url
        self.assertEqual(int(url.query.data['bx']), 50)
        self.assertEqual(int(url.query.data['by']), 75)
        self.assertEqual(int(url.query.data['bw']), 100)
        self.assertEqual(int(url.query.data['bh']), 200)
        self.assertEqual(int(url.query.data['w']), 300)
        self.assertEqual(int(url.query.data['h']), 400)
        self.assertEqual(int(url.query.data['ppi']), 500)
        self.assertEqual(int(url.query.data['hz']), 800)        

    def test_xorgdisplay(self):
        if sys.platform=="linux2":
            d = DisplayDevice.create("xorgdisplay:")
            self.assertEqual(d.url.scheme, "xorgdisplay")
            self.assertIsInstance(d.bounds, Bounds)
            self.assertIsInstance(d.size, Size)
            self.assertIsInstance(d.resolution[0], float)
            self.assertIsInstance(d.resolution[1], float)
            self.assertIsInstance(d.refreshrate, float)
            self.assertIsInstance(d.url, URL)
        # FIXME: Until pylibpointing do not handle c++ exceptions better do
        # not cause them
        #else:
        #    self.assertRaises(ValueError, DisplayDevice.create, "xorgdisplay:")

    def test_windisplay(self):
        if sys.platform=="win32":
            d = DisplayDevice.create("windisplay:")
            self.assertEqual(d.url.scheme, "windisplay")
            self.assertIsInstance(d.bounds, Bounds)
            self.assertIsInstance(d.size, Size)
            self.assertIsInstance(d.resolution[0], float)
            self.assertIsInstance(d.resolution[1], float)
            self.assertIsInstance(d.refreshrate, float)
            self.assertIsInstance(d.url, URL)
        # FIXME: Until pylibpointing do not handle c++ exceptions better do
        # not cause them
        #else:
        #    self.assertRaises(ValueError, DisplayDevice.create, "windisplay:")

# -------------------------------------------------------------------

def suite():
    tests = list(t for t in dir(CreateCase) \
                     if t.startswith("test_"))
    return unittest.TestSuite(map(CreateCase, tests))    

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
