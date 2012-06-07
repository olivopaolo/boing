# -*- coding: utf-8 -*-
#
# boing/nodes/multitouch/__init__.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from PyQt4 import QtGui

from boing import Offer, Request, Functor
from boing.utils import assertIsInstance

def attrToRequest(attributes):
    """Transform contact attributes to a full Request.
    Example: 
      "rel_pos,rel_speed|boundingbox.rel_size" becomes
      "diff.added,updated.contacts.*.rel_pos,rel_speed|diff.added,updated.contacts.*.boundingbox.rel_size"
    """
    request = ""
    for attr in attributes.split("|"):
        if request: request += "|"
        request += "diff.added,updated.contacts.*.%s"%attr
    return Request(request)

class Calibration(Functor):
    """Apply a 4x4 transformation matrix to each target value."""

    Identity = QtGui.QMatrix4x4()
    Right = QtGui.QMatrix4x4(0.0,-1.0, 0.0, 1.0, 
                             1.0, 0.0, 0.0, 0.0, 
                             0.0, 0.0, 1.0, 0.0,
                             0.0, 0.0, 0.0, 1.0)
    Inverted = QtGui.QMatrix4x4(-1.0, 0.0, 0.0, 1.0, 
                                 0.0,-1.0, 0.0, 1.0, 
                                 0.0, 0.0, 1.0, 0.0,
                                 0.0, 0.0, 0.0, 1.0)
    Left = QtGui.QMatrix4x4( 0.0, 1.0, 0.0, 0.0, 
                            -1.0, 0.0, 0.0, 1.0, 
                             0.0, 0.0, 1.0, 0.0,
                             0.0, 0.0, 0.0, 1.0)

    def __init__(self, request, blender, matrix=Identity, parent=None):
        super().__init__(request, Functor.TUNNELING, blender, parent=parent)
        self._matrix = assertIsInstance(matrix, QtGui.QMatrix4x4)

    def matrix(self):
        return self._matrix

    def setMatrix(self, matrix):
        matrix = assertIsInstance(matrix, QtGui.QMatrix4x4)

    def _process(self, sequence, producer):
        for operands in sequence:
            yield tuple(self._applyMatrix(operands))

    def _applyMatrix(self, operands):
        for name, value in operands:
            if len(value)==2:
                point = self.matrix()*QtGui.QVector4D(value[0], 
                                                      value[1], 
                                                      0, 
                                                      1)
                value = [point.x(), point.y()]
            elif len(value)==3:
                point = self.matrix()*QtGui.QVector4D(value[0], 
                                                      value[1], 
                                                      value[2], 
                                                      1)
                value = [point.x(), point.y(), point.z()]
            elif len(value)==4:
                point = self.matrix()*QtGui.QVector4D(*value)
                value = [point.x(), point.y(), point.z(), point.w()]
            yield (name, value)


    @staticmethod
    def buildMatrix(values):
        return QtGui.QMatrix4x4(*values)


            
