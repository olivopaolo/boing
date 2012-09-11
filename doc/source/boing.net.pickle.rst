====================================================
 :mod:`boing.net.pickle` --- Python pickle encoding
====================================================

.. module:: boing.net.pickle
   :synopsis: Python pickle encoding

The module :mod:`boing.net.pickle` provides methods and classes for
supporting Python object serialization. It uses the python pickle
standard module.

Encoder and Decoder classes provide a standard interface for the pickle
encoding.

.. function:: encode(obj, protocol=None)

   Return the pickled representation of *obj* as a bytes object.

   The optional protocol argument tells the pickler to use the given
   protocol; supported protocols are 0, 1, 2, 3. The default protocol
   is 3; a backward-incompatible protocol designed for Python 3.0.

   Specifying a negative protocol version selects the highest
   protocol version supported. The higher the protocol used, the more
   recent the version of Python needed to read the pickle produced.

.. function:: decode(data)

   Read a pickled object hierarchy from the bytes object *data*
   and return the reconstituted object hierarchy specified therein.

   The protocol version of the pickle is detected automatically, so
   no protocol argument is needed. Bytes past the pickled object’s
   representation are ignored.

.. class:: Encoder

   The Encoder is able to serialize Python objects into pickle
   bytestrings.

   .. method:: encode(obj)

      Return the pickled representation of *obj* as a bytes object.

      The optional protocol argument tells the pickler to use the given
      protocol; supported protocols are 0, 1, 2, 3. The default protocol
      is 3; a backward-incompatible protocol designed for Python 3.0.

      Specifying a negative protocol version selects the highest
      protocol version supported. The higher the protocol used, the more
      recent the version of Python needed to read the pickle produced.

   .. method:: reset

      NOP method.

.. class:: Decoder

   The Decoder object is able to decode pickle bytestrings into
   the corrispetive objects hierarchy.

   .. method:: decode(obj)

      Read a pickled object hierarchy from the bytes object *data*
      and return the reconstituted object hierarchy specified therein.

      The protocol version of the pickle is detected automatically, so
      no protocol argument is needed. Bytes past the pickled object’s
      representation are ignored.

   .. method:: reset

      Reset the slip internal buffer.

