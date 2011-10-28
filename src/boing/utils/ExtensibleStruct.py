# -*- coding: utf-8 -*-
#
# boing/utils/ExtensibleStruct.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections

class ExtensibleStruct(object):

    def __init__(self, **keyvalues):
        object.__setattr__(self, "_ExtensibleStruct__info", [])
        for key, value in keyvalues.items():
            self.__setattr__(key, value)

    def duplicate(self):
        return self.__class__(**self.getInfo())

    def set(self, key, value):
        self.__setattr__(key, value)
        return self

    def setdefault(self, key, valueOrFunction, *args):
        try:
            return self.__dict__[key]
        except KeyError:
            if isinstance(valueOrFunction, collections.Callable):
                valueOrFunction = valueOrFunction(*args)
            self.__setattr__(key, valueOrFunction)
            return valueOrFunction

    def get(self, key, defvalue=None):
        return self.__dict__.get(key, defvalue)

    def getInfo(self):
        f = lambda t, l= self.__info: t[0] in l
        return dict(filter(f, self.__dict__.items()))

    def getSignature(self, withTypes=False):
        if withTypes:
            return dict([(key, type(value)) for key, value in self.getInfo().items()])
        else:
            return frozenset(self.__info)

    def conformsToSignature(self, signature):
        for key in signature:
            if key not in self.__info: return False
        return True
   
    def __setattr__(self, key, value):
        if key in self.__info:
            object.__setattr__(self, key, value)
        elif key in self.__class__.__dict__.keys():
            raise AttributeError("Can't set attribute '%s': name already used by %s"%(key, self.__class__.__name__))
        else:
            object.__setattr__(self, key, value)
            self.__info.append(key)

    def __str__(self):
        info = self.getInfo()
        keys = list(info.keys())
        keys.sort()
        output = ", ".join(["%s=%s"%(k,repr(info[k])) for k in keys])
        return "%s(%s)"%(self.__class__.__name__,output)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.getInfo()==other.getInfo()

    def __ne__(self, other):
        return not self.__eq__(other)
