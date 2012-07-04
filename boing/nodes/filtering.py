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

class _Factory:

    def __init__(self, factorymethod):
        self.__factorymethod = factorymethod

    def create(self):
        return self.__factorymethod()


def getFunctorFactory(uri):
    """Returns a factory that can be used to build functor objects."""
    uri = str(uri)
    if uri.startswith("/noise/"):
        noise = NoiseFunctor(uri.replace("/noise/", "", 1))
        functor = lambda value: value + noise()
        rvalue = _Factory(lambda: functor)
    else:
        test = createFilter(uri)
        rvalue = _Factory(lambda: createFilter(uri))
    return rvalue
