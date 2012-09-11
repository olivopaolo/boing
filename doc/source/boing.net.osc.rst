=======================================
 :mod:`boing.net.osc` --- OSC encoding
=======================================

.. module:: boing.net.osc
   :synopsis: OSC encoding

The module :mod:`boing.net.osc` provides methods and classes for
handling OSC formatted messages.

Encoder and Decoder classes provide a standard interface for the OSC
encoding.

.. class:: Encoder

   The Encoder is able to encode OSC packet objects into byte strings.

   .. method:: encode(obj)

      Return the bytestring obtained from serializing the OSC
      packet *obj*.


   .. method:: reset

      NOP method.

.. class:: Decoder

   The Decoder is able to convert valid byte string objects into
   OSC Packet objects.

   .. method:: decode(obj)

      Return the list of OSC packets decoded from the bytestring
      *obj*.

   .. method:: reset

      Reset the slip internal buffer.

