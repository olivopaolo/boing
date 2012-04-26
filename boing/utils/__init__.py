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
        if ref in memo: rvalue = memo[ref]
        else:
            rvalue = quickdict()
            memo[ref] = rvalue
            for key, value in self.items():
                rvalue[key] = copy.deepcopy(value, memo)
        return rvalue

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
    if isinstance(obj, list) or isinstance(obj, tuple):
        print("%s["%(" "*level*indent), end="", file=fd)
        if maxdepth is None or level<maxdepth:
            for i, value in enumerate(obj):
                if (isinstance(value, list) or isinstance(value, tuple) \
                        or isinstance(value, collections.Mapping)) \
                        and value:
                    print("", file=fd)
                    _deepDump(value, fd, level+1, maxdepth, indent)
                else:
                    if i>0: print(" "*(level*indent+1), end="", file=fd)
                    print(repr(value), end="", file=fd)
                if i<len(obj)-1: print(",", file=fd)
            print("]", end="", file=fd)
        else:
            print("...]", end="", file=fd)
    elif isinstance(obj, collections.Mapping):
        print("%s{"%(" "*level*indent), end="", file=fd)
        keys = list(obj.keys())
        keys.sort()
        if maxdepth is None or level<maxdepth:
            for i, key in enumerate(keys):
                value = obj[key]
                if i>0: print(" "*(level*indent+1), end="", file=fd)
                if (isinstance(value, list) or isinstance(value, tuple) \
                        or isinstance(value, collections.Mapping)) \
                        and value:
                    print("%s:"%repr(key), file=fd)
                    _deepDump(value, fd, level+1, maxdepth, indent)
                else:
                    print("%s: %s"%(repr(key), repr(value)), end="", file=fd)
                if i<len(obj)-1: print(",", file=fd)
            print("}", end="", file=fd)
        else:
            for i, key in enumerate(keys):
                if i>0: print(" "*(level*indent+1), end="", file=fd)
                print("%s: ..."%repr(key), end="", file=fd)
                if i<len(obj)-1:
                    print(",", file=fd)
            print("}", end="", file=fd)
    else:
        print(repr(obj), file=fd)
    if level==0: print(file=fd)

