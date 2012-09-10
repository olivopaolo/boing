# -*- coding: utf-8 -*-
#
# setup.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import sys

from setuptools import setup, find_packages

props = dict(
    name = "boing",
    version = "0.3.0",
    packages = find_packages(),
    entry_points = {'console_scripts': ["boing = boing.run"]},
    test_suite = "boing.test.run",
    author = "Paolo Olivo",
    author_email = "olivopaolo@tiscali.it",
    url = "http://github.com/olivopaolo/boing",
    description = """
Boing is a toolkit designed to support the development of multi-touch
and gesture enabled applications.

It enables to create pipelines for connecting different input sources to
multiple target destinations (e.g. applications, logs, etc.)  and
eventually process the data before being dispatched.""",
    license = "GPLv2",
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)'
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.2',
        'Topic :: Scientific/Engineering :: Human Machine Interfaces',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: Utilities',
        ],
)

if sys.platform in ("linux2", "darwin"):
    props["install_requires"] = (
        'numpy>=1.6.1',
        'pyparsing>=1.5.6',
        )

setup(**props)
