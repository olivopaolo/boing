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
import tempfile
import time
import unittest

txtfilepath = os.path.join(os.path.dirname(__file__),
                           "data", "file.txt")
config_filtersfilepath = os.path.join(os.path.dirname(__file__),
                                      "data", "config-filters.txt")
my_mt_tablefilepath = os.path.join(os.path.dirname(__file__),
                                   "data", "my-mt-table.txt")

cmds = (
    # Command line arguments
    (tuple(), 0), # empty
    (('-h', ), 0),
    (('--help',), 0),
    (('--version', ), 0),
    (('nop:', '-G'), 0),
    (('nop:', '-G', 'grapher:stdout'), 0),
    (('nop:', '-G', 'wrong'), 1),
    (('nop:', '-C'), 0),
    (('nop:', '-C', '127.0.0.1:8888'), 0),
    (('nop:', '-C', 'wrong'), 1),
    (('nop:', '-T'), 0),
    (('nop:', '-T', '10'), 0),
    (('nop:', '-T', 'wrong'), 2),
    (('nop:', '-L', 'INFO'), 0),
    (('nop:', '-L', 'wrong'), 1),
    (('nop:', '-f'), 0),
    (('nop:', '--no-gui'), 0),
    # First steps tutorial
    (('in.tuio://:3333 + viz:', ), 0),
    (('in.tuio://:3333 + (viz: | dump:)', ), 0),
    (('in.tuio://:3333 + (viz: | dump:?request=..contacts)', ), 0),
    (('(in.tuio://:3333 | in.tuio://:3334) + (viz: | out.tuio://127.0.0.1:3335)', ), 0),
    (('in.tuio://:3333 + (filtering: + calib:?screen=left + edit:?source=filtered | nop:) + viz:', ), 0),
    # Configurations tutorial
    (('conf:%s'%config_filtersfilepath, ), 0),
    (('conf:%s + (viz: | rec: | out.tuio://127.0.0.1:3334)'%my_mt_tablefilepath, ), 0),
    )

class Test_returncode_only(unittest.TestCase):

    def setUp(self):
        self.out = tempfile.TemporaryFile('w+')
        self.err = tempfile.TemporaryFile('w+')

    def test_no_exceptions(self):
        for cmd, expected in cmds:
            self.proc = subprocess.Popen(("boing",)+cmd,
                                         stdout=self.out,
                                         stderr=self.err)
            # Loop: poll and sleep
            for i in range(100):
                returncode = self.proc.poll()
                if returncode is not None : break
                time.sleep(0.01)
            else:
                # Timeout: stop and wait
                self.proc.send_signal(signal.SIGINT)
                returncode = self.proc.wait()
            # Check return code
            self.assertEqual(returncode, expected)

# -------------------------------------------------------------------
# Data Redirection tests

class Test_run_redirection(unittest.TestCase):

    def setUp(self):
        self.out = tempfile.TemporaryFile('w+')
        self.err = tempfile.TemporaryFile('w+')

    def test_in_std_out_std(self):
        self.proc = subprocess.Popen(("boing", "in: + out:"),
                                     stdin=open(txtfilepath),
                                     stdout=self.out,
                                     stderr=self.err)
        # Loop: poll and sleep
        for i in range(50):
            returncode = self.proc.poll()
            if returncode is not None : break
            time.sleep(0.01)
        else:
            # Timeout: stop and wait
            self.proc.send_signal(signal.SIGINT)
            returncode = self.proc.wait()
        self.assertFalse(returncode)
        # Check return code
        self.assertFalse(returncode)
        # Compare output
        self.out.seek(0)
        result = self.out.read()
        with open(txtfilepath) as fd:
            expected = fd.read()
        self.assertEqual(result, expected)

    def test_in_file_out_std(self):
        self.proc = subprocess.Popen(("boing", "in:%s + out:"%txtfilepath),
                                     stdout=self.out,
                                     stderr=self.err)
        # Loop: poll and sleep
        for i in range(50):
            returncode = self.proc.poll()
            if returncode is not None : break
            time.sleep(0.01)
        else:
            # Timeout: stop and wait
            self.proc.send_signal(signal.SIGINT)
            returncode = self.proc.wait()
        # Check return code
        self.assertFalse(returncode)
        # Compare output
        self.out.seek(0)
        result = self.out.read()
        with open(txtfilepath) as fd:
            expected = fd.read()
        self.assertEqual(result, expected)

    def test_in_std_out_file(self):
        tempout = tempfile.NamedTemporaryFile()
        self.proc = subprocess.Popen(("boing", "in: + out:%s"%tempout.name),
                                     stdin=open(txtfilepath),
                                     stdout=self.out,
                                     stderr=self.err)
        # Loop: poll and sleep
        for i in range(50):
            returncode = self.proc.poll()
            if returncode is not None : break
            time.sleep(0.01)
        else:
            # Timeout: stop and wait
            self.proc.send_signal(signal.SIGINT)
            returncode = self.proc.wait()
        # Check return code
        self.assertFalse(returncode)
        # Compare output
        tempout.seek(0)
        result = tempout.read()
        with open(txtfilepath, "rb") as fd:
            expected = fd.read()
        self.assertEqual(result, expected)

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

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
