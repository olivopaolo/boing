# -*- coding: utf-8 -*-
#
# boing/filtering/filter/NoiseFunctor.py -
#
# Authors: Paolo Olivo (paolo.olivo@inria.fr)
#          Nicolas Roussel (nicolas.roussel@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import math
import parser

import numpy

class NoiseFunctor:

    # See http://docs.scipy.org/doc/numpy/reference/routines.random.html
    #
    #   numpy.random.gumbel    loc=0.0, scale=1.0, size=None
    #   numpy.random.laplace   loc=0.0, scale=1.0, size=None
    #   numpy.random.logistic  loc=0.0, scale=1.0, size=None
    #   numpy.random.normal    loc=0.0, scale=1.0, size=None
    #   numpy.random.uniform   low=0.0, high=1.0, size=1
    #   numpy.random.wald      mean, scale, size=None

    def __init__(self, expression):
        self.__expression = self.__code = None
        self.expression = expression

    @property
    def expression(self):
        return self.__expression

    @expression.setter
    def expression(self, expression):
        code = parser.expr(expression).compile()
        self.__expression = expression
        self.__code = code

    def __call__(self):
        return eval(self.__code)

    def __str__(self):
        return "[Noise functor: "+self.__expression+"]"

if __name__=="__main__":
    import traceback
    nf = NoiseFunctor("numpy.random.normal(0.0, 1.0)")
    print(nf.expression)
    print(nf())
    '''try:
        nf.expression = "toto+ - +"
    except:
        traceback.print_exc()
    print(nf.expression)
    print(nf())'''
