# -*- coding: utf-8 -*-
#
# boing/filtering/filter/ExponentialFilter.py -
#
# Authors: Paolo Olivo (paolo.olivo@inria.fr)
#          Nicolas Roussel (nicolas.roussel@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import math

import numpy

# -----------------------------------------------------------------------

class SingleExponentialFilter:

    """
    See http://www.itl.nist.gov/div898/handbook/pmc/section4/pmc431.htm
    """

    def __init__(self, alpha, variant="predict"):
        self.__setAlpha(alpha)
        if variant=="predict":
            self.__predict = True
        elif variant=="lowpass":
            self.__predict = False
        else:
            raise ValueError("variant should be 'predict' or 'lowpass'")
        self.__y = self.__s = None

    def __setAlpha(self, alpha):
        alpha = float(alpha)
        if alpha<=0 or alpha>1.0:
            raise ValueError("alpha (%s) should be in (0.0, 1.0]"%alpha)
        self.__alpha = alpha

    def __call__(self, value, timestamp=None, alpha=None):
        if alpha is not None:
            self.__setAlpha(alpha)
        #print "SEF: alpha =", self.__alpha
        if self.__y is None:
            s = value
        else:
            if self.__predict:
                s = self.__alpha*self.__y + (1.0-self.__alpha)*self.__s
            else:
                s = self.__alpha*value + (1.0-self.__alpha)*self.__s
        self.__y = value
        self.__s = s
        return s

    def lastValue(self):
        return self.__y

    def lastEstimate(self):
        return self.__s

    def getURL(self):
        return "fltr:/exponential/single?alpha=%s"%self.__alpha

    def __str__(self):
        return self.getURL()

    @staticmethod
    def generateConfigurations(step):
        nbsteps = int(math.floor((1.0-step)/step))
        return ["fltr:/exponential/single?alpha=%s"%(step*(i+1)) for i in range(nbsteps+1)]

    @staticmethod
    def randomConfiguration():
        alpha = 1.0 - numpy.random.random_sample() # will be in (0.0, 1.0]
        return "fltr:/exponential/single?alpha=%s"%alpha

# -----------------------------------------------------------------------

class DoubleExponentialFilter:

    """
    See http://www.itl.nist.gov/div898/handbook/pmc/section4/pmc433.htm
    """

    def __init__(self, alpha, gamma):
        alpha, gamma = float(alpha), float(gamma)
        if alpha<0 or alpha>1.0:
            raise ValueError("alpha (%s) should be in [0.0, 1.0]"%alpha)
        if gamma<0 or gamma>1.0:
            raise ValueError("gamma (%s) should be in [0.0, 1.0]"%gamma)
        self.__alpha = float(alpha)
        self.__gamma = float(gamma)
        self.__y = self.__s = None

    def __call__(self, value, timestamp=None):
        if self.__y is None:
            s = value
            b = 0 # FIXME
        else:
            s = self.__alpha*value + (1.0-self.__alpha)*(self.__s+self.__b)
            b = self.__gamma*(s-self.__s) + (1.0-self.__gamma)*self.__b
        self.__y = value
        self.__b = b
        self.__s = s
        return s

    def getURL(self):
        return "fltr:/exponential/double?alpha=%s&gamma=%s"%(self.__alpha, self.__gamma)

    def __str__(self):
        return self.getURL()

    @staticmethod
    def generateConfigurations(step):
        configs = []
        nbsteps = int(math.floor(1.0/step))
        for ia in range(nbsteps+1):
            for ig in range(nbsteps+1):
                if ia==0 and ig==0: continue
                configs.append((ia*step, ig*step))
        return ["fltr:/exponential/double?alpha=%s&gamma=%s"%args for args in configs]

    @staticmethod
    def randomConfiguration(**params):
        if "alpha" not in params:
            params["alpha"] = 1.0 - numpy.random.random_sample() # FIXME: will be in (0.0, 1.0]
        if "gamma" not in params:
            params["gamma"] = 1.0 - numpy.random.random_sample() # FIXME: will be in (0.0, 1.0]
        return "fltr:/exponential/double?alpha=%s&gamma=%s"%(params["alpha"],params["gamma"])

# -----------------------------------------------------------------------

class DESPFilter:

    """
    J. J. LaViola. Double exponential smoothing: an alternative to
    kalman filter-based predictive tracking. In Proceedings of
    EGVE'03, ACM (2003), 199–206.

    See http://www.cs.brown.edu/people/jjl/ptracking/ptracking.html
    """

    def __init__(self, alpha, tau=1):
        alpha = float(alpha)
        if alpha<0 or alpha>=1.0:
            raise ValueError("alpha (%s) should be in [0.0, 1.0)"%alpha)
        self.__alpha = float(alpha)
        if int(tau)<=0:
            raise ValueError("tau (%s) should be >0"%alpha)
        self.__tau = int(tau)
        self.__hatxiprev = None
        self.__hatxi2prev = None

    def __call__(self, value, timestamp=None):
        if self.__hatxiprev is None:
            hatxi = value
        else:
            hatxi = self.__alpha * value + (1.0-self.__alpha) * self.__hatxiprev
        self.__hatxiprev = hatxi
        if self.__hatxi2prev is None:
            hatxi2 = hatxi
        else:
            hatxi2 = self.__alpha * hatxi + (1.0-self.__alpha) * self.__hatxi2prev
        self.__hatxi2prev = hatxi2
        return (2.0 + (self.__alpha*self.__tau)/(1.0-self.__alpha)) * hatxi \
               - (1.0 + (self.__alpha*self.__tau)/(1.0-self.__alpha)) * hatxi2

    def getURL(self):
        return "fltr:/exponential/desp?alpha=%g&tau=%d"%(self.__alpha,self.__tau)

    def __str__(self):
        return self.getURL()

    @staticmethod
    def generateConfigurations(step, mintau=1, maxtau=1):
        nbsteps = int(math.floor((0.999-step)/step))
        return ["fltr:/exponential/desp?alpha=%g&tau=%d"%(step*i,tau) \
                for i in range(nbsteps+1) for tau in range(mintau, maxtau+1)]

    @staticmethod
    def randomConfiguration(mintau=1, maxtau=1):
        alpha = numpy.random.random_sample() # will be in [0.0, 1.0)
        tau = numpy.random.random_integers(mintau, maxtau)
        return "fltr:/exponential/desp?alpha=%g&tau=%d"%(alpha, tau)
