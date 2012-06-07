# -*- coding: utf-8 -*-
#
# boing/net/json.py
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import base64
import logging
import json as _json
import datetime
import struct

import boing.utils as utils
import boing.net.ntp as ntp

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
        rvalue = utils.quickdict(dct)
    return rvalue

def encode(obj):
    return _json.dumps(obj, cls=_ProductEncoder, separators=(',',':')) 

def decode(data):
    return _json.loads(data, object_hook=_productHook)
