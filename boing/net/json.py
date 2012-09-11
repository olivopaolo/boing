# -*- coding: utf-8 -*-
#
# boing/net/json.py
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

"""The module :mod:`boing.net.json` provides methods and classes for
supporting JSON object serialization. It uses the python json standard
module, but it provides a default solution for serializing bytestrings
and datetime.datetime objects.

Encoder and Decoder classes provide a standard interface for the JSON
encoding.

"""

import base64
import logging
import json as _json
import datetime
import struct

from boing.net import ntp

class _ProductEncoder(_json.JSONEncoder):
    def default(self, obj):
        serializable = None
        if isinstance(obj, bytearray) or isinstance(obj, bytes):
            serializable = {"__bytes__": base64.b64encode(obj).decode()}
        elif isinstance(obj, datetime.datetime):
            pack = struct.pack("d", ntp.datetime2ntp(obj))
            serializable = {"__ntp__": base64.b64encode(pack).decode()}
        else:
            try:
                serializable = _json.JSONEncoder.default(self, obj)
            except TypeError as e:
                logger = logging.getLogger("boing.net.json._ProductEncoder")
                logger.warning(str(e))
        return serializable

def _productHook(dct):
    if "__bytes__" in dct:
        rvalue = base64.b64decode(dct["__bytes__"].encode())
    elif "__ntp__" in dct:
        pack = base64.b64decode(dct["__ntp__"].encode())
        ntptime = struct.unpack("d", pack)[0]
        rvalue = ntp.ntp2datetime(ntptime)
    else:
        rvalue = dct
    return rvalue

def encode(obj):
    """Return a string containing the json serialization of *obj*."""
    return _json.dumps(obj, cls=_ProductEncoder, separators=(',',':'))

def decode(string):
    """Return the object obtained for decoding *string* using the JSON
    decoding."""
    return _json.loads(string, object_hook=_productHook)

# -------------------------------------------------------------------

from boing.net import Encoder as _AbstractEncoder
from boing.net import Decoder as _AbstractDecoder

class Encoder(_AbstractEncoder):
    """The Encoder is able to serialize standard data types into json strings.

    """
    def encode(self, obj):
        """Return a string containing the json serialization of *obj*."""
        return encode(obj)

    def reset(self):
        """NOP method."""
        pass

class Decoder(_AbstractDecoder):
    """The Decoder object is able to decode json strings into the
    corrispetive python objects.

    """
    def decode(self, string):
        """Return the list of object obtained from the deserialization
        of *string*."""
        return decode(string),

    def reset(self):
        """NOP method."""
        pass
