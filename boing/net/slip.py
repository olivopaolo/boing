# -*- coding: utf-8 -*-
#
# boing/net/slip.py
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

# Based on
#     Nonstandard for transmission of IP datagrams over serial lines: SLIP
#     http://tools.ietf.org/html/rfc1055

"""The slip module provides methods and classes for supporting the
SLIP protocol encoding and decoding.

"""

END     = 0o300 # indicates end of packet
ESC     = 0o333 # indicates byte stuffing
ESC_END = 0o334 # ESC ESC_END means END data byte
ESC_ESC = 0o335 # ESC ESC_ESC means ESC data byte

def encode(data):
    """Return a slip encoded version of *data*."""
    encoded = bytearray()
    encoded.append(END)
    for c in data:
        if c==END:
            encoded.append(ESC)
            encoded.append(ESC_END)
        elif c==ESC:
            encoded.append(ESC)
            encoded.append(ESC_ESC)
        else:
            encoded.append(c)
    encoded.append(END)
    return bytes(encoded)

def decode(data, previous=None):
    """Return the list of bytearrays obtained from the slip decoding
    of *data* followed by the undecoded bytes. If previous is not
    None, *data* is appended to previous before decoding.
    A typical usage would be::

      buffer = bytearray()
      decoded, buffer = decode(data, buffer)

    """
    decoded = previous if previous else bytearray()
    result, prev = [], None
    for c in data:
        if prev==ESC:
            if c==ESC_END:
                decoded.append(END)
            elif c==ESC_ESC:
                decoded.append(ESC)
            else:
                decoded.append(bytes((c,))) # protocol violation...
        else:
            if c==END:
                if decoded: result.append(bytes(decoded))
                decoded = bytearray()
            elif c==ESC:
                pass
            else:
                decoded.append(c)
        prev = c
    return result, decoded

# -------------------------------------------------------------------

from boing.net import Encoder as _AbstractEncoder
from boing.net import Decoder as _AbstractDecoder

class Encoder(_AbstractEncoder):
    """The Encoder is able to produce slip encoded version of byte strings.

    """
    def encode(self, obj):
        """Return a slip encoded version of the byte string *obj*."""
        return encode(obj)

    def reset(self):
        """NOP method."""
        pass

class Decoder(_AbstractDecoder):
    """The Decoder object is able to decode slip encoded byte strings
    into the their internal components.

    """
    def __init__(self):
        super().__init__()
        self._buffer = None

    def decode(self, obj):
        """Return the list of bytearrays obtained from the slip
        decoding of *obj*."""
        items, self._buffer = decode(obj, self._buffer)
        return items

    def reset(self):
        """Reset the slip internal buffer."""
        self._buffer = None
