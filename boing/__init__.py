# -*- coding: utf-8 -*-
#
# boing/__init__.py -
#
# Authors: Paolo Olivo (paolo.olivo@inria.fr)
#          Nicolas Roussel (nicolas.roussel@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

MAJOR = 0
MINOR = 2
VERSION = "%d.%d"%(MAJOR,MINOR)

from boing.nodes.loader import create
