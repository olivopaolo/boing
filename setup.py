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
On demand producer-consumer architecture for connecting different
sources (e.g. devices, sockets, files, etc.) to different outputs, while
applying flexible data processing.""",
    license = "GPLv2",
    install_requires = ['numpy>=1.6.1'],
)
