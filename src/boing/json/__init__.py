# -*- coding: utf-8 -*-
#
# boing/json/__init__.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import json
import datetime

from boing.utils.ExtensibleTree import ExtensibleTree
from boing.time import ntp

class ProductEncoder(json.JSONEncoder):
    def default(self, obj):
        serializable = None
        if isinstance(obj, ExtensibleTree):
            l = lambda v: self.default(v) \
                if isinstance(v, ExtensibleTree) \
                or isinstance(v, datetime.datetime) \
                else v
            serializable = dict((k, l(v)) for (k,v) in obj.items())
            serializable["__tree__"] = True
        elif isinstance(obj, datetime.datetime):
            serializable = {"__ntp__": ntp.datetime2ntp(obj)}
        else:
            serializable = json.JSONEncoder.default(self, obj)
        return serializable

def productHook(dct):
    if "__tree__" in dct:
        tree = ExtensibleTree()
        for k, v in dct.items():
            if k!="__tree__":
                if k.isdecimal(): tree[int(k)] = v
                else: tree[k] = v
        return tree
    if "__ntp__" in dct:
        return ntp.ntp2datetime(dct["__ntp__"])
    return dct

