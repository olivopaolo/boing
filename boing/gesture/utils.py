# -*- coding: utf-8 -*-
#
# boing/gesture/utils.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

"""The boing.gesture.utils module contains common method used by
different recognizers.
"""

def boundingBox(points):
    """Return the tuple (minx, miny, maxx, maxy) defining the bounding
    box for *points*."""
    minx = min(p.x for p in points)
    maxx = max(p.x for p in points)
    miny = min(p.y for p in points)
    maxy = max(p.y for p in points)
    return minx, miny, maxx, maxy

def updateBoundingBox(bb1, bb2):
    """Return the tuple (minx, miny, maxx, maxy) defining the bounding
    box containing the bounding boxes *bb1* and *bb2*."""
    minx = min(bb1[0], bb2[0])
    miny = min(bb1[1], bb2[1])
    maxx = max(bb1[2], bb2[2])
    maxy = max(bb1[3], bb2[3])
    return minx, miny, maxx, maxy
