=========================================
 :mod:`boing.net.json` --- JSON encoding
=========================================

.. module:: boing.net.json
   :synopsis: JSON encoding

The module :mod:`boing.net.json` provides methods and classes for
supporting JSON object serialization. It uses the python json standard
module, but it provides a default solution for serializing bytestrings
and datetime.datetime objects.

Encoder and Decoder classes provide a standard interface for the JSON
encoding.


.. function:: encode(obj)

   Return a string containing the json serialization of *obj*.

.. function:: decode(string)

   Return the object obtained for decoding *string* using the JSON
   decoding.

.. class:: Encoder

   The Encoder is able to serialize standard data types into json strings.

   .. method:: encode(obj)

      Return a string containing the json serialization of *obj*.

   .. method:: reset

      NOP method.

.. class:: Decoder

   The Decoder object is able to decode json strings into the
   corrispetive python objects.

   .. method:: decode(string)

      Return the list of object obtained from the deserialization
      of *string*.

   .. method:: reset

      NOP method.

