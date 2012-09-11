==============================================================
 :mod:`boing.gesture.utils` --- Recognizers' common utilities
==============================================================

.. module:: boing.gesture.utils
   :synopsis: Recognizers' common utilities

The boing.gesture.utils module contains common method used by
different recognizers.

.. function:: boundingBox(points)

   Return the tuple (minx, miny, maxx, maxy) defining the bounding
   box for *points*.


.. function:: updateBoundingBox(bb1, bb2)

   Return the tuple (minx, miny, maxx, maxy) defining the bounding box
   containing the bounding boxes *bb1* and *bb2*.
