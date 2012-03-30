#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# boing/test/run.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import unittest

def additional_tests(modules=[]):

    tests = []
    if not modules or 'dns_sd' in modules:
        from boing.test.net import test_dns_sd
        tests += test_dns_sd.suite()
    if not modules or 'core' in modules:
        from boing.test.core import test_ReactiveObject
        tests += test_ReactiveObject.suite()
    if not modules or 'json' in modules:
        from boing.test.net import test_json
        tests += test_json.suite()
    if not modules or 'osc' in modules:
        from boing.test.net import test_osc
        tests += test_osc.suite()
    if not modules or 'slip' in modules:
        from boing.test.net import test_slip
        tests += test_slip.suite()
    if not modules or 'tcp' in modules:
        from boing.test.net import test_tcp
        tests += test_tcp.suite()
    if not modules or 'udp' in modules:
        from boing.test.net import test_udp
        tests += test_udp.suite()
    if not modules or 'utils' in modules:
        from boing.test.utils import test_QPath, test_display
        tests += test_QPath.suite()
        tests += test_display.suite()

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
 dns_sd, core, json, osc, slip, tcp, udp, utils""")

    parser.add_argument("module", metavar="MODULE", nargs="*", default=[],
                        help="module to be tested")
    args = parser.parse_args()
    runner = unittest.TextTestRunner()
    runner.run(additional_tests(args.module))
