# -*- coding: utf-8 -*-
#
# boing/utils/__init__.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import copy

class quickdict(dict):

    def __getattr__(self, key):
        if key in self: return dict.__getitem__(self, key)
        else:
            rvalue = quickdict()
            self[key] = rvalue
            return rvalue

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        if key in self: del self[key]
        else:
            dict.__delattr__(self, key)

    def __getitem__(self, key):
        if key in self: return dict.__getitem__(self, key)
        else:
            rvalue = quickdict()
            self[key] = rvalue
            return rvalue

    def copy(self):
        return self.__copy__()

    def __copy__(self):
        return quickdict(self)

    def __deepcopy__(self, memo):
        ref = id(self)
        if ref in memo:
            return memo[ref]
        else:
            dup = quickdict()
            memo[ref] = dup
            for k,v in self.items():
                dup[k] = copy.deepcopy(v, memo)
            return dup

    def __repr__(self):
        return "quickdict(%s)"%dict.__repr__(self)

# -------------------------------------------------------------------

def deepadd(obj, other, diff=False, reuse=False):
    rvalue = quickdict() if diff else None
    for key, value in other.items():
        if key in obj:
            # Inner case
            objvalue = obj[key]
            if isinstance(value, collections.Mapping) \
                    and isinstance(objvalue, collections.Mapping):
                inner = deepadd(objvalue, value, diff, reuse)                  
                if inner: rvalue[key] = inner
        else:
            obj[key] = value if reuse else copy.deepcopy(value)
            if diff: rvalue[key] = value
    return rvalue


def deepupdate(obj, other, diff=False, reuse=False):
    rvalue = quickdict() if diff else None
    for key, value in other.items():
        if key in obj:
            # Inner case
            objvalue = obj[key]
            if isinstance(value, collections.Mapping) \
                    and isinstance(objvalue, collections.Mapping):
                inner = deepupdate(objvalue, value, diff, reuse)
                if inner: rvalue[key] = inner
            elif objvalue!=value:
                obj[key] = value if reuse else copy.deepcopy(value)
                if diff: rvalue[key] = value
        else:
            obj[key] = value if reuse else copy.deepcopy(value)
            if diff: rvalue[key] = value
    return rvalue


def deepremove(obj, other, diff=False):
    rvalue = quickdict() if diff else None
    for key, value in other.items():
        if key in obj:
            # Inner case
            objvalue = obj[key]
            if isinstance(value, collections.Mapping) \
                    and isinstance(objvalue, collections.Mapping):
                inner = deepremove(objvalue, value, diff)
                if inner: rvalue[key] = inner
            else:
                del obj[key]
                if diff: rvalue[key] = None
    return rvalue

# -------------------------------------------------------------------

def deepDump(obj, fd, maxdepth=None, indent=4):
    return _deepDump(obj, fd, 0, maxdepth, indent)

def _deepDump(obj, fd, level, maxdepth, indent):
    if isinstance(obj, list):
        fd.write(" "*(level*indent))
        fd.write("[")
        if maxdepth is None or level<maxdepth:
            for i, value in enumerate(obj):
                if isinstance(value, collections.Mapping) \
                        or isinstance(value, list):
                    _deepDump(value, fd, level+1, maxdepth, indent)
                else:
                    if i>0: fd.write(" "*(level*indent+1))
                    fd.write(repr(value))
                if i<len(obj)-1:
                    fd.write(",\n")
                else:
                    fd.write("]")
        else:
            fd.write("...]")
    elif isinstance(obj, collections.Mapping):
        fd.write(" "*(level*indent))
        fd.write("{")
        if maxdepth is None or level<maxdepth:
            for i, (key, value) in enumerate(obj.items()):
                if i>0: fd.write(" "*(level*indent+1))
                if isinstance(value, collections.Mapping) \
                        or isinstance(value, list):
                    fd.write("%s:\n"%repr(key))
                    _deepDump(value, fd, level+1, maxdepth, indent)
                else:
                    fd.write("%s: %s"%(repr(key), repr(value)))
                if i<len(obj)-1:
                    fd.write(",\n")
                else:
                    fd.write("}")
        else:
            for i, key in enumerate(obj.keys()):
                if i>0: fd.write(" "*(level*indent+1))
                fd.write("%s: ..."%repr(key))
                if i<len(obj)-1:
                    fd.write(",\n")
                else:
                    fd.write("}")
    else:
        fd.write(repr(obj))
    if level==0: fd.write("\n")

