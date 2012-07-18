# -*- coding: utf-8 -*-
#
# boing/nodes/multitouch/__init__.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import datetime

from PyQt4 import QtGui

from boing.core import Offer, QRequest, Functor
from boing.utils import assertIsInstance, quickdict

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
    return QRequest(request)

# -------------------------------------------------------------------

class Calibration(Functor):
    """The Calibration functor processes the requested data by applind
    a 4x4 transformation matrix to each target value."""

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

    def __init__(self, request, blender=Functor.MERGECOPY,
                 matrix=Identity, parent=None):
        super().__init__(request, Functor.TUNNELING, blender, parent=parent)
        self._matrix = assertIsInstance(matrix, QtGui.QMatrix4x4)

    def matrix(self):
        """Return the 4x4 matrix that is applied to the incoming data."""
        return self._matrix

    def setMatrix(self, matrix):
        """Set the 4x4 matrix used to process the incoming
        data. *matrix* must be a QtGui.QMatrix4x4."""
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
        """Return the 4x4 matrix obtained from the list of *values*."""
        return QtGui.QMatrix4x4(*values)

# -------------------------------------------------------------------

class StrokeFinder(Functor):

    def __init__(self, blender=Functor.MERGECOPY, parent=None):
        super().__init__(
            QRequest("diff.*.contacts|source|timetag"),
            Offer(dict(gestures=dict(id=dict(stroke=list())))),
            blender, parent=parent)
        self._buffer = {}
        self.cls = "UNKNOWN"

    def _process(self, sequence, producer):
        for operands in sequence:
            source = timetag = add = update = remove = None
            for key, value in operands:
                if key=="source": source = value
                elif key=="timetag": timetag = value
                elif "added" in key: add = value
                elif "updated" in key: update = value
                else: remove = value
            if source is None: source = id(producer)
            if timetag is None: timetag = datetime.datetime.now()
            record = self._buffer.setdefault(source, {})
            if add is not None:
                for key, value in add.items():
                    record[key] = [(timetag, value)]
            if update is not None:
                for key, value in update.items():
                    stroke = record.setdefault(key, [])
                    stroke.append((timetag, value))
            if remove is not None:
                results = []
                for key in remove.keys():
                    stroke = record.pop(key)
                    # FIXME: this should be done in a separated Node.
                    l = lambda o: quickdict(t=o[0],
                                            x=o[1]['rel_pos'][0]*100,
                                            y=o[1]['rel_pos'][1]*100)
                    stroke = tuple(map(l, stroke))
                    # ---
                    results.append(("gestures.%s"%key, dict(stroke=stroke,
                                                            cls=self.cls)))
                if results: yield results


class GestureRecognizer(Functor):

    def __init__(self, recognizer, blender=Functor.MERGECOPY, parent=None):
        super().__init__(QRequest("gestures.*.stroke"),
                         Offer(dict(gestures=dict(id=dict(cls=object())))),
                         blender, parent=parent)
        self._recognizer = recognizer
        self._learning = False
        self._trainingset = []

    def isLearning(self):
        return self._learning

    def startLearning(self):
        self._recognizer.reset()
        self.setRequest(QRequest("gestures.*.stroke,cls"))
        self._learning = True

    def stopLearning(self):
        self._recognizer.buildRecognizer(self._trainingset)
        del self._trainingset[:]
        self.setRequest(QRequest("gestures.*.stroke"))
        self._learning = False

    def _process(self, sequence, producer):
        for operands in sequence:
            if self.isLearning():
                print(operands)
            else:
                results = list()
                for key, stroke in operands:
                    result = self._recognizer.recognize(stroke)
                    if result is not None:
                        results.append(("gestures.%s.cls"%key.split(".")[1],
                                       result["cls"]))
                if results: yield results
