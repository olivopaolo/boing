=======================================
 :mod:`boing.net.osc` --- OSC encoding
=======================================

.. module:: boing.net.osc
   :synopsis: OSC encoding

The module :mod:`boing.net.osc` provides methods and classes for
handling OSC_ formatted messages.

Container classes
=================

.. class:: Packet

   Abstract base container of OSC data.

   .. method:: encode()

      .. decorator:: @abc.abstractmethod

      Return the encoded representation of this packet.

   .. method:: debug(out, indent="")

      .. decorator:: @abc.abstractmethod

      Write to *out* a string representation of the OSC packet. The
      argument *indent* can be used to format the output.


.. class:: EncodedPacket(data)

   :class:`Packet` object representing the encoded object *data*.

   .. method:: decode()

      Return the decoded representation of this packet, that is an
      instance of the class :class:`Bundle` or :class:`Message`.

.. class:: Message(address, typetags="", *arguments)

   :class:`Packet` object representing an OSC Message. The argument
   *address* must be a string begginning with the character ``/``
   (forward slash). The argument *typetags* must be a string composed
   by sequence of characters corresponding exactly to the sequence of
   OSC arguments in the given message. *arguments* is the list of
   object contained in the OSC Message.

   .. attribute:: address

      String beginning with the character ``/`` (forward slash).

   .. attribute:: typetags

      String composed by a sequence of characters corresponding
      exactly to the sequence of OSC arguments in the given message.

   .. attribute:: arguments

      List of the arguments of the message.

.. class:: Bundle(timetag, elements)

   :class:`Packet` object representing an OSC Bundle. The argument *timetag*
   must be a :class:`datetime.datetime` instance or ``None``, while
   *elements* should be the list of :class:`Packet` objects contained
   in the bundle.

   .. attribute:: timetag

      ``None`` or a :class:`datetime.datetime` instance.

   .. attribute:: elements

      List of :class:`Packet` objects contained into the bundle.


Encoding and decoding
=====================

.. function:: decode(data, source=None)

   Return the :class:`Packet` object decoded from the bytestring
   *data*. The argument *source* can be specified to set the packet
   source.

The classes :class:`Encoder` and :class:`Decoder` provide a standard
interface for the OSC encoding.

.. class:: Encoder

   Implements the :class:`boing.net.Encoder` interface for encoding
   OSC packet objects into byte strings.

   .. method:: encode(obj)

      Return the bytestring obtained from serializing the OSC
      packet *obj*.


   .. method:: reset

      NOP method.

.. class:: Decoder

   Implements the :class:`boing.net.Decoder` interface for converting
   valid byte string objects into OSC Packet objects.

   .. method:: decode(obj)

      Return the list of OSC packets decoded from the bytestring
      *obj*.

   .. method:: reset

      NOP method.

Usage example
=============

::

   >>> import sys
   >>> import boing.net.osc as osc
   >>> source = osc.Message("/tuio/2Dcur", "ss", "source", "test")
   >>> alive = osc.Message("/tuio/2Dcur", "ss", "alive", "1")
   >>> bundle = osc.Bundle(None,
                           (source, alive,
                            osc.Message("/tuio/2Dcur", "si", "fseq", 1)))
   >>> data = bundle.encode()
   >>> print(data)
   b'#bundle\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00 /tuio/2Dcur\x00,ss\x00source\x00\x00test\x00\x00\x00\x00\x00\x00\x00\x1c/tuio/2Dcur\x00,ss\x00alive\x00\x00\x001\x00\x00\x00\x00\x00\x00\x1c/tuio/2Dcur\x00,si\x00fseq\x00\x00\x00\x00\x00\x00\x00\x01'
   >>> packet = osc.decode(data)
   >>> print(packet)
   <Bundle instance at 0x1b756d0 [@None, 3 element(s)]>
   >>> packet.debug(sys.stdout)
   Bundle IMMEDIATELY
    | /tuio/2Dcur ss 'source' 'test'
    | /tuio/2Dcur ss 'alive' '1'
    | /tuio/2Dcur si 'fseq' 1


.. _OSC: http://opensoundcontrol.org/spec-1_0
