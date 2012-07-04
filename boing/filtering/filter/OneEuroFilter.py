# -*- coding: utf-8 -*-
#
# boing/filtering/filter/OneEuroFilter.py -
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

# ----------------------------------------------------------------------------

from boing.filtering.filter.ExponentialFilter import SingleExponentialFilter

class OneEuroFilter:

    # FIXME: find a better name for beta and dcutoff?
    def __init__(self, freq, mincutoff=1.0, beta=0.0, dcutoff=1.0):
        if freq<=0:
            raise ValueError("freq should be >0")
        if mincutoff<=0:
            raise ValueError("mincutoff should be >0")
        if dcutoff<=0:
            raise ValueError("dcutoff should be >0")
        self.__freq = float(freq)
        self.__mincutoff = float(mincutoff)
        self.__beta = float(beta)
        self.__dcutoff = float(dcutoff)
        self.__x = SingleExponentialFilter(self.__alpha(self.__mincutoff), variant="lowpass")
        self.__dx = SingleExponentialFilter(self.__alpha(self.__dcutoff), variant="lowpass")
        self.__lasttime = None

    def __alpha(self, cutoff):
        te    = 1.0 / self.__freq
        tau   = 1.0 / (2*math.pi*cutoff)
        return  1.0 / (1.0 + tau/te)

    def __call__(self, x, timestamp=None):
        # ---- update the sampling frequency based on timestamps
        if self.__lasttime and timestamp:
            self.__freq = 1.0 / (timestamp-self.__lasttime)
            #print "OneEuroFilter: updating frequency, now %s Hz"%self.__freq
        self.__lasttime = timestamp
        # ---- estimate the current variation per second
        prev_x = self.__x.lastValue()
        dx = 0 if prev_x is None else (x-prev_x)*self.__freq
        edx = self.__dx(dx, timestamp, alpha=self.__alpha(self.__dcutoff))
        # ---- use it to update the cutoff frequency
        cutoff = self.__mincutoff + self.__beta*math.fabs(edx)
        # ---- filter the given value
        #print "cutoff:", cutoff, "alpha:", self.__alpha(cutoff)
        return self.__x(x, timestamp, alpha=self.__alpha(cutoff))

    def getURL(self):
        return "fltr:oneeuro?dcutoff=%s&freq=%s&mincutoff=%s&beta=%s"%(self.__dcutoff, self.__freq, self.__mincutoff, self.__beta)

    def __str__(self):
        return self.getURL()

    @staticmethod
    def generateConfigurations(freq, cutoffstep, maxcutoff, betastep, maxbeta, dcutoffs=[1.0]):
        nbcutoffsteps = int(math.floor((maxcutoff-cutoffstep)/cutoffstep))
        cutoffs = [(i+1)*cutoffstep for i in range(nbcutoffsteps+1)]
        betas = [i*betastep for i in range(int(math.floor(maxbeta/betastep)+1))]
        if dcutoffs is None: dcutoffs = cutoffs
        configs = [(freq, mincutoff, beta, dcutoff) for mincutoff in cutoffs for beta in betas for dcutoff in dcutoffs]
        return ["fltr:oneeuro?freq=%s&mincutoff=%s&beta=%s&dcutoff=%s"%args for args in configs]

    @staticmethod
    def randomConfiguration(freq, **params):
        # FIXME: we're in dire need of heuristics and fancy probability distributions...
        maxcutoff = params.setdefault("maxcutoff", 20) # FIXME: this is an arbitrary choice
        if "mincutoff" not in params:
            # will be in (0.0, maxcutoff]
            params["mincutoff"] = maxcutoff - maxcutoff*numpy.random.random_sample()
        if "beta" not in params:
            maxbeta = params.get("maxbeta", 100.0)
            # will be in [0.0, maxbeta)
            params["beta"] = maxbeta*numpy.random.random_sample()
        if "dcutoff" not in params:
            # will be in (0.0, freq]
            params["dcutoff"] = freq - freq*numpy.random.random_sample()
        return "fltr:oneeuro?freq=%s&mincutoff=%s&beta=%s&dcutoff=%s"%(freq, params["mincutoff"], params["beta"], params["dcutoff"])

# ----------------------------------------------------------------------------

if __name__=="__main__":
    frequency = 120
    configs = OneEuroFilter.generateConfigurations(frequency,
                                                   cutoffstep=0.5, maxcutoff=frequency/3,
                                                   betastep=0.1, maxbeta=40.0)
    print(len(configs), "configurations")
    for config in configs: print("  ", config)
    print()
    print(OneEuroFilter.randomConfiguration(frequency))
