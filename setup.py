# -*- coding: utf-8 -*-
#
# setup.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from setuptools import setup, find_packages

setup(
    name = "boing",
    version = "0.2.0",
    packages = find_packages(),
    entry_points = {'console_scripts': ["boing = boing.run"]},
    test_suite = "boing.test.run",
    author = "Paolo Olivo",
    author_email = "paolo.olivo@inria.fr",
    description = """
Boing is a toolkit designed to support the development of multi-touch
and gesture enabled applications.

It enables to create pipelines for connecting different input sources to
multiple target destinations (e.g. applications, logs, etc.)  and
eventually process the data before being dispatched.""",
    license = "GPLv2",
    install_requires = [
        'numpy>=1.6.1',
        'pyparsing>=1.5.6'
        ],
)
