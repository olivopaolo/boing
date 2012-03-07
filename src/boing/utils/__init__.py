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

    def __str__(self):
        return dict.__str__(self)

    def __repr__(self):
        return "quickdict(%s)"%dict.__repr__(self)

# -------------------------------------------------------------------

def deepadd(obj, other, diff=False):
    rvalue = dict() if diff else None
    for key, value in other.items():
        if key in obj:
            # Inner case
            objvalue = obj[key]
            if isinstance(value, collections.Mapping) \
                    and isinstance(objvalue, collections.Mapping):
                inner = deepadd(objvalue, value, diff)                  
                if inner: rvalue[key] = inner
        else:
            obj[key] = copy.deepcopy(value)
            if diff: rvalue[key] = value
    return rvalue


def deepupdate(obj, other, diff=False):
    rvalue = dict() if diff else None
    for key, value in other.items():
        if key in obj:
            # Inner case
            objvalue = obj[key]
            if isinstance(value, collections.Mapping) \
                    and isinstance(objvalue, collections.Mapping):
                inner = deepupdate(objvalue, value, diff)
                if inner: rvalue[key] = inner
            elif objvalue!=value:
                obj[key] = copy.deepcopy(value)
                if diff: rvalue[key] = value
        else:
            obj[key] = copy.deepcopy(value)
            if diff: rvalue[key] = value
    return rvalue


def deepremove(obj, other, diff=False):
    rvalue = dict() if diff else None
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
