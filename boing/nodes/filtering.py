# -*- coding: utf-8 -*-
#
# boing/nodes/filtering.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from boing.filtering.filter import createFilter
from boing.filtering.noise import NoiseFunctor
from boing.utils.url import URL

class _Factory:

    def __init__(self, factorymethod):
        self.__factorymethod = factorymethod

    def create(self):
        return self.__factorymethod()


def getFunctorFactory(uri):
    """Returns a factory that can be used to build functor objects."""
    url = URL(str(uri))
    if url.scheme=="fltr":
        test = createFilter(uri)
        rvalue = _Factory(lambda: createFilter(uri))
    elif url.scheme=="noise":
        noise = NoiseFunctor(url.opaque)
        functor = lambda value: value + noise()
        rvalue = _Factory(lambda: functor)
    else:
        raise Exception("Invalid filtering URI: %s"%uri)
    return rvalue
