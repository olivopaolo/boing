# -*- coding: utf-8 -*-
#
# boing/net/json.py
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import base64
import json
import datetime
import struct

import boing.utils.ntp as ntp

class ProductEncoder(json.JSONEncoder):
    def default(self, obj):
        serializable = None
        if isinstance(obj, bytes):
            serializable = {"__bytes__": base64.b64encode(obj).decode()}
        elif isinstance(obj, datetime.datetime):
            pack = struct.pack("d", ntp.datetime2ntp(obj))
            serializable = {"__ntp__": base64.b64encode(pack).decode()}
        else:
            serializable = json.JSONEncoder.default(self, obj)
        return serializable

def productHook(dct):
    if "__bytes__" in dct:
        return base64.b64decode(dct["__bytes__"].encode())
    if "__ntp__" in dct:
        pack = base64.b64decode(dct["__ntp__"].encode())
        ntptime = struct.unpack("d", pack)[0]
        return ntp.ntp2datetime(ntptime)
    return dct

