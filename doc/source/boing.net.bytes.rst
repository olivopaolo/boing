=============================================
 :mod:`boing.net.bytes` --- UNICODE encoding
=============================================

.. module:: boing.net.bytes
   :synopsis: UNICODE encoding

The :mod:`boing.net.bytes` module implements the adapter design
pattern by providing the standard string encoding functionalities as
Encoder and Decoder objects.

.. function:: encode(string, encoding="utf-8", errors="strict")

   Return an encoded version of *string* as a bytes object. Default
   encoding is 'utf-8'. *errors* may be given to set a different
   error handling scheme. The default for errors is 'strict',
   meaning that encoding errors raise a UnicodeError. Other
   possible values are 'ignore', 'replace', 'xmlcharrefreplace',
   'backslashreplace'

.. function:: decode(data, encoding="utf-8", errors="strict")

   Return a string decoded from the given bytes. Default
   *encoding* is 'utf-8'. *errors* may be given to set a different
   error handling scheme. The default for errors is 'strict', meaning
   that encoding errors raise a UnicodeError. Other possible values
   are 'ignore', 'replace' and any other name registered via
   codecs.register_error().


.. class:: Encoder(encoding="utf-8", errors="strict")

   The Encoder is able to produce encoded version of string objects as
   byte objects.

   .. method:: encode(string)

      Return an encoded version of *string* as a bytes object.

   .. method:: reset

      NOP method.

.. class:: Decoder(encoding="utf-8", errors="strict")

   The Decoder is able to convert byte objects into strings.

   .. method:: decode(data)

      Return the list of strings decoded from the given bytes.

   .. method:: reset

      NOP method.
