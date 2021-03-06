#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# boing/test/run.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import sys
import unittest

def additional_tests(modules=[]):

    tests = []
    if not modules:
        from boing.test import test_run
        tests += test_run.suite()
    if not modules or 'utils' in modules:
        from boing.test.utils import test__init__, test_querypath, test_url
        tests += test__init__.suite()
        tests += test_querypath.suite()
        tests += test_url.suite()
    if not modules or 'core' in modules:
        from boing.test.core import test_observer, test_economy
        tests += test_observer.suite()
        tests += test_economy.suite()
    if not modules or 'net' in modules:
        from boing.test.net import test__init__
        tests += test__init__.suite()
        from boing.test.net import test_json
        tests += test_json.suite()
        from boing.test.net import test_pickle
        tests += test_pickle.suite()
        from boing.test.net import test_osc
        tests += test_osc.suite()
        from boing.test.net import test_slip
        tests += test_slip.suite()
        from boing.test.net import test_tcp
        tests += test_tcp.suite()
        from boing.test.net import test_udp
        tests += test_udp.suite()
    if not modules or 'gesture' in modules:
        from boing.test.gesture import test_rubine
        tests += test_rubine.suite()
    if not modules or 'filtering' in modules:
        from boing.test.filtering import test_filter
        tests += test_filter.suite()
    if not modules or 'nodes' in modules:
        from boing.test.nodes import test_loader
        tests += test_loader.suite()
        from boing.test.nodes import test_logger
        tests += test_logger.suite()
    return unittest.TestSuite(tests)


if __name__=="__main__":
    import argparse

    # Parse arguments
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
If no module is specified, all modules are tested; otherwise only the
specified modules will be executed.

Available modules:
 core, filtering, gesture, net, nodes, utils""")

    parser.add_argument("module", metavar="MODULE", nargs="*", default=[],
                        help="module to be tested")
    args = parser.parse_args()
    runner = unittest.TextTestRunner()
    runner.run(additional_tests(args.module))
