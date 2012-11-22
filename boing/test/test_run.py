#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# boing/test/test_run.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import itertools
import os.path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

txtfile = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       "data", "file.txt"))
configtestfile = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                              "data", "config-filters.txt"))
sysprefix = "/" if sys.platform=="win32" else ""

cmds = (
    # Command line arguments
    (("-h", ), 0),
    (("--help",), 0),
    (("nop:", "-G"), 0),
    (("nop:", "-G", "grapher:stdout"), 0),
    (("nop:", "-G", "grapher.udp://[::1]:8888"), 0),
    (("nop:", "-G", "grapher:?request=id,active&hz=0"), 0),
    (("nop:", "-G", "wrong"), 1),
    (("nop:", "-C"), 0),
    (("nop:", "-C", "127.0.0.1:8888"), 0),
    (("nop:", "-C", "wrong"), 1),
    (("nop:", "-T"), 0),
    (("nop:", "-T", "10"), 0),
    (("nop:", "-T", "wrong"), 1),
    (("nop:", "-L", "INFO"), 0),
    (("nop:", "-L", "wrong"), 1),
    (("nop:", "-f"), 0),
    (("nop:", "--no-gui"), 0),
    # First steps tutorial
    (("in.tuio://:3333 + viz:", ), 0),
    (("in.tuio://:3333 + (viz: | dump:)", ), 0),
    (("in.tuio://:3333 + (viz: | dump:?request=..contacts)", ), 0),
    (("(in.tuio://:3333 | in.tuio://:3334) + (viz: | out.tuio://127.0.0.1:3335)", ), 0),
    (("in.tuio://:3333 + (filtering: + calib:?screen=left + edit:?source=filtered | nop:) + viz:", ), 0),
    # Configurations tutorial
    (("conf:%s%s"%(sysprefix, configtestfile), ), 0),
    )

class Test_returncode_only(unittest.TestCase):

    def test_no_exceptions(self):
        for cmd, expected in cmds:
            out = tempfile.TemporaryFile("w+")
            err = tempfile.TemporaryFile("w+")
            self.proc = subprocess.Popen(("boing", "--no-raise", "-L", "ERROR")+cmd,
                                         stdout=out,
                                         stderr=err)
            # Loop: poll and sleep
            for i in range(20):
                returncode = self.proc.poll()
                if returncode is not None : break
                time.sleep(0.02)
            else:
                # Timeout: stop and wait
                while returncode is None:
                    self.proc.send_signal(signal.SIGTERM)
                    returncode = self.proc.poll()
                    if returncode is None : time.sleep(0.1)
            # Check stderr is empty
            if expected==0:
                err.seek(0)
                self.assertFalse(err.read())

# -------------------------------------------------------------------
# Data Redirection tests

class Test_run_redirection(unittest.TestCase):

    def setUp(self):
        self.out = tempfile.TemporaryFile("w+")
        self.err = tempfile.TemporaryFile("w+")
        self.maxDiff = None

    def test_in_std_out_std(self):
        if sys.platform=="linux2": # Windows do not support node ``in:``
            cmd = "boing in:+out: -L ERROR --no-raise"
            self.proc = subprocess.Popen(cmd.split(),
                                         stdin=open(txtfile),
                                         stdout=self.out,
                                         stderr=self.err)
            # Loop: poll and sleep
            for i in range(10):
                returncode = self.proc.poll()
                if returncode is not None : break
                time.sleep(0.1)
            else:
                # Timeout: stop and wait
                self.proc.send_signal(signal.SIGTERM)
                returncode = self.proc.wait()
            # Compare output
            self.out.seek(0)
            result = self.out.read()
            with open(txtfile) as fd:
                expected = fd.read()
            self.assertEqual(result, expected)
            # Check stderr is empty
            self.err.seek(0)
            self.assertFalse(self.err.read())

    def test_in_file_out_std(self):
        cmd = "boing in://%s%s+out: -L ERROR --no-raise"%(sysprefix, txtfile)
        self.proc = subprocess.Popen(cmd.split(),
                                     stdout=self.out,
                                     stderr=self.err)
        # Loop: poll and sleep
        for i in range(30):
            returncode = self.proc.poll()
            if returncode is not None : break
            time.sleep(0.1)
        else:
            # Timeout: stop and wait
            self.proc.send_signal(signal.SIGTERM)
            returncode = self.proc.wait()
        # Compare output
        self.out.seek(0)
        result = self.out.read()
        with open(txtfile) as fd:
            expected = fd.read()
        self.assertEqual(result, expected)
        # Check stderr is empty
        self.err.seek(0)
        self.assertFalse(self.err.read())

    def test_in_std_out_file(self):
        if sys.platform=="linux2": # Windows do not support node ``in:``
            tempout = tempfile.NamedTemporaryFile()
            cmd = "boing in:+out://%s -L ERROR --no-raise"%tempout.name
            self.proc = subprocess.Popen(cmd.split(),
                                         stdin=open(txtfile),
                                         stdout=self.out,
                                         stderr=self.err)
            # Loop: poll and sleep
            for i in range(15):
                returncode = self.proc.poll()
                if returncode is not None : break
                time.sleep(0.1)
            else:
                # Timeout: stop and wait
                self.proc.send_signal(signal.SIGTERM)
                returncode = self.proc.wait()
            # Compare output
            tempout.seek(0)
            result = tempout.read()
            with open(txtfile, "rb") as fd:
                expected = fd.read()
            self.assertEqual(result, expected)
            # Check stderr is empty
            self.err.seek(0)
            self.assertFalse(self.err.read())

# -------------------------------------------------------------------

def suite():
    testcases = (
        Test_returncode_only,
        Test_run_redirection,
        )
    return unittest.TestSuite(itertools.chain(
            *(map(t, filter(lambda f: f.startswith("test_"), dir(t))) \
                  for t in testcases)))

# -------------------------------------------------------------------

if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())
