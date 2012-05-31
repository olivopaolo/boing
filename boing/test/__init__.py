# -*- coding: utf-8 -*-
#
# boing/test/__init__.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import sys
import unittest

from PyQt4 import QtCore

class QtBasedTest(unittest.TestCase):

    def setUp(self):
        self.app = QtCore.QCoreApplication(sys.argv)

    def tearDown(self):
        self.app.exit()
        self.app = None
