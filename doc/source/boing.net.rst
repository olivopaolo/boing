====================================================
 :mod:`boing.net` --- Networking and encoding tools
====================================================

.. module:: boing.net
   :synopsis: Networking and encoding tools

The module :mod:`boing.net` provides classes and methods to ease the
usage of sockets and networking encodings, like for example JSON, OSC,
SLIP, etc.

.. class:: boing.net.Encoder

   The Encoder class is the abstract base class for implementing
   the encoders of all the different encodings.

.. class:: boing.net.Decoder

   The Decoder class is the abstract base class for implementing
   the decoders of all the different encodings.

   The Decoder class implements the composite pattern. Many decoders
   can be put in sequence into a single composed decoder using the
   sum operator.


Each encoding has been implemented in a different submodule:

.. toctree::
   boing.net.bytes
   boing.net.slip
   boing.net.json
   boing.net.osc
   boing.net.pickle


Common networking utilities:

.. toctree::
   boing.net.ip
   boing.net.tcp
   boing.net.udp
   boing.net.ntp