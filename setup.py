# -*- coding: utf-8 -*-
#
# setup.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

# --- Compile PyQt4 .ui files ---
import os.path
from PyQt4 import uic
uic.compileUiDir(os.path.join(os.path.dirname(__file__), "boing"), True)
# ---

from setuptools import setup, find_packages
import boing

long_desc = """Boing is a toolkit designed to support the development
of multi-touch and gesture enabled applications.

It enables to create pipelines for connecting different input sources to
multiple target destinations (e.g. applications, logs, etc.)  and
eventually process the data before being dispatched."""

kwargs = dict(
    name = "boing",
    version = boing.__version__,
    packages = find_packages(),
    entry_points = {"console_scripts": ["boing = boing.run"]},
    test_suite = "boing.test.run",
    package_data = {
        'boing.nodes.player': ['icons/*'],
        'boing.test': ['data/*'],
        },

    author = "Paolo Olivo",
    author_email = "boing@librelist.com",
    url = "http://boing.readthedocs.org",
    description = long_desc,
    license = "GPLv2",
    classifiers = (
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.2",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: User Interfaces",
        "Topic :: Utilities",
        ),
)

import sys
if sys.platform in ("linux2", "darwin"):
    kwargs["install_requires"] = (
        'pyparsing>=1.5.6',
        )

setup(**kwargs)
