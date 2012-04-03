# -*- coding: utf-8 -*-
#
# boing/extra/filtering.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import libfilter.filter
from libfilter.noise.NoiseFunctor import NoiseFunctor

from boing.utils.url import URL

class _Factory(object):

    def __init__(self, factorymethod):
        self.__factorymethod = factorymethod

    def create(self):
        return self.__factorymethod()


def getFunctorFactory(uri):
    """Returns a factory that can be used to build functor objects."""
    url = URL(str(uri))
    if url.scheme=="fltr":
        test = libfilter.filter.createFilter(uri)
        rvalue = _Factory(lambda: libfilter.filter.createFilter(uri))
    elif url.scheme=="noise":
        noise = NoiseFunctor(url.opaque)
        functor = lambda value: value + noise()
        rvalue = _Factory(lambda: functor)
    else:
        raise Exception("Invalid libfilter URI: %s"%uri)
    return rvalue
