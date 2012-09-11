=========================================
 :mod:`boing.net.slip` --- SLIP encoding
=========================================

.. module:: boing.net.slip
   :synopsis: SLIP encoding

The module :mod:`boing.net.slip` provides methods and classes for
supporting the SLIP protocol encoding and decoding.


.. function:: encode(data)

   Return a slip encoded version of *data*.

.. function:: decode(data, previous=None)

   Return the list of bytearrays obtained from the slip decoding
   of *data* followed by the undecoded bytes. If previous is not
   None, *data* is appended to previous before decoding.
   A typical usage would be::

      buffer = bytearray()
      decoded, buffer = decode(data, buffer)


.. class:: Encoder

   The Encoder is able to produce slip encoded version of byte strings.

   .. method:: encode(obj)

      Return a slip encoded version of the byte string *obj*.

   .. method:: reset

      NOP method.

.. class:: Decoder

   The Decoder object is able to decode slip encoded byte strings
   into the their internal components.

   .. method:: decode(obj)

      Return the list of bytearrays obtained from the slip
      decoding of *obj*.

   .. method:: reset

      Reset the slip internal buffer.
