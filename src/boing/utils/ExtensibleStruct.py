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

class ExtensibleStruct(collections.MutableMapping):

    def __init__(self, **keyvalues):
        object.__setattr__(self, "_ExtensibleStruct__info", set())
        for key, value in keyvalues.items():
            self.__setattr__(key, value)

    def copy(self):
        return self.__class__(**dict(self.items()))

    def get(self, key, defvalue=None):
        return self.__dict__.get(key, defvalue)

    def items(self):
        return ((key, value) for key, value in self.__dict__.items() \
                    if key in self.__info)

    def values(self):
        return (value for key,value in self.__dict__.items() \
                    if key in self.__info)

    def keys(self):
        return iter(self.__info)

    def signature(self, withTypes=False):
        if withTypes:
            return dict([(key, type(value)) for key, value in self.items()])
        else:
            return frozenset(self.__info)

    def conformsToSignature(self, signature):
        for key in signature:
            if key not in self.__info: return False
        return True

    def setdefault(self, key, valueOrFunction, *args):
        try:
            return self.__dict__[key]
        except KeyError:
            if isinstance(valueOrFunction, collections.Callable):
                valueOrFunction = valueOrFunction(*args)
            self.__setattr__(key, valueOrFunction)
            return valueOrFunction

    # ---------------------------------------------------------------------
    #  Customizing attribute access
        
    def __setattr__(self, key, value):
        if key in self.__info:
            object.__setattr__(self, key, value)
        elif key in self.__class__.__dict__.keys():
            raise AttributeError("Can't set attribute '%s': name already used by %s"%(key, self.__class__.__name__))
        else:
            object.__setattr__(self, key, value)
            self.__info.add(key)

    def __delattr__(self, key):
        if key in self.__info: 
            self.__info.remove(key)
            object.__delattr__(self, key)
        else: 
            raise AttributeError(
                "Cannot remove item '%s': name reserved by %s"%(
                    key, self.__class__.__name__))

    # ---------------------------------------------------------------------
    #  Basic customization

    def __str__(self):
        info = dict(self.items())
        keys = list(info.keys())
        keys.sort()
        output = ", ".join(["%s=%s"%(k,repr(info[k])) for k in keys])
        return "%s(%s)"%(self.__class__.__name__,output)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return dict(self.items())==dict(other.items())

    def __ne__(self, other):
        return not self.__eq__(other)

    # ---------------------------------------------------------------------
    #  Emulating container type
    
    def __len__(self):
        return len(self.__info)

    def __iter__(self):
        return iter(self.__info)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __delitem__(self, key):
        self.__delattr__(key)

    def __contains__(self, key):
        return key in self.__info

