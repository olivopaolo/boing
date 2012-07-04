# -*- coding: utf-8 -*-
#
# boing/filtering/filter/MovingWindowFilter.py -
#
# Authors: Paolo Olivo (paolo.olivo@inria.fr)
#          Nicolas Roussel (nicolas.roussel@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import numpy

# -----------------------------------------------------------------------

class MovingWindowFilter:

    def __init__(self, name, f, winsize):
        if winsize<1:
            raise ValueError("winsize should be >0")
        self.__name = name
        self.__filter = f
        self.__winsize = int(winsize)
        self.__window = numpy.array([])

    def __call__(self, value, timestamp=None):
        if len(self.__window)<self.__winsize:
            self.__window = numpy.append(self.__window, value)
        else:
            self.__window = numpy.roll(self.__window, -1)
            self.__window[-1] = value
        return self.__filter(self.__window)

    def getURL(self):
        return "fltr:moving/%s?winsize=%s"%(self.__name, self.__winsize)

    def __str__(self):
        return self.getURL()

    @staticmethod
    def generateConfigurations(subclass, maxwinsize, step):
        return ["fltr:moving/%s?winsize=%d"%(subclass,i) for i in range(1, maxwinsize, step)]

    @staticmethod
    def randomConfiguration(subclass, maxwinsize):
        winsize = numpy.random.random_integers(1, maxwinsize)
        return "fltr:moving/%s?winsize=%d"%(subclass,winsize)

# -----------------------------------------------------------------------

class MovingMeanFilterSmart(MovingWindowFilter):

    def __init__(self, winsize):
        if winsize<1:
            raise ValueError("winsize should be >0")
        self.__winsize = int(winsize)
        self.__window = numpy.array([])
        self.__last = None

    def __call__(self, value, timestamp=None):
        if len(self.__window)<self.__winsize or self.__last is None:
            self.__window = numpy.append(self.__window, value)
            result = numpy.mean(self.__window)
        else:
            poppedvalue = self.__window[0]
            self.__window = numpy.roll(self.__window, -1)
            self.__window[-1] = value
            result = self.__last - poppedvalue/self.__winsize + value/self.__winsize
        self.__last = result
        return result

    def getURL(self):
        return "fltr:moving/%s?winsize=%s"%(self.__name, self.__winsize)

    def __str__(self):
        return self.getURL()

    @staticmethod
    def generateConfigurations(maxwinsize, step):
        return ["fltr:moving/mean?winsize=%d"%i for i in range(1, int(maxwinsize), int(step))]

    @staticmethod
    def randomConfiguration(maxwinsize):
        winsize = numpy.random.random_integers(1, int(maxwinsize))
        return "fltr:moving/mean?winsize=%d"%winsize

class MovingMeanFilter(MovingWindowFilter):

    def __init__(self, winsize):
        super().__init__("mean", numpy.mean, int(winsize))

    @staticmethod
    def generateConfigurations(maxwinsize, step=1):
        return MovingWindowFilter.generateConfigurations("mean", int(maxwinsize), int(step))

    @staticmethod
    def randomConfiguration(maxwinsize):
        return MovingWindowFilter.randomConfiguration("mean", int(maxwinsize))

class MovingMedianFilter(MovingWindowFilter):

    def __init__(self, winsize):
        super().__init__("median", numpy.median, int(winsize))

    @staticmethod
    def generateConfigurations(maxwinsize, step=1):
        return MovingWindowFilter.generateConfigurations("median", int(maxwinsize), int(step))

    @staticmethod
    def randomConfiguration(maxwinsize):
        return MovingWindowFilter.randomConfiguration("median", int(maxwinsize))

# -----------------------------------------------------------------------

if __name__=="__main__":
    mm1 = MovingMeanFilterBis(134)
    mm2 = MovingMeanFilter(134)
    for i in range(1000):
        value = numpy.random.sample()
        f1, f2 = mm1(value), mm2(value)
        print(f1==f2, f1-f2, f1, f2)

if __name__=="__main__2":
    configs = MovingMeanFilter.generateConfigurations(20, 3)
    print(len(configs), "configurations")
    for config in configs: print("  ", config)
    print()
    print(MovingMedianFilter.randomConfiguration(1000))
