# -*- coding: utf-8 -*-
#
# boing/filtering/filter/__init__.py -
#
# Authors: Paolo Olivo (paolo.olivo@inria.fr)
#          Nicolas Roussel (nicolas.roussel@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import urllib.parse

from boing.filtering.filter.MovingWindowFilter import MovingMeanFilter, MovingMedianFilter
from boing.filtering.filter.ExponentialFilter import SingleExponentialFilter, DoubleExponentialFilter, DESPFilter
from boing.filtering.filter.KalmanFilter import LinearKalmanFilter, ConstantValueKalmanFilter, DerivativeBasedKalmanFilter
from boing.filtering.filter.OneEuroFilter import OneEuroFilter

def __registerURLs():
    try:
        registered = urllib.parse.libfilter_filter_registerURLs
    except AttributeError:
        urllib.parse.uses_query.insert(0, "fltr")
        urllib.parse.libfilter_filter_registerURLs = 1

def createFilter(uri):
    __registerURLs()
    uri = urllib.parse.urlsplit(uri, "fltr")
    if uri.scheme!="fltr":
        raise ValueError("Bad URL scheme ('%s') for a filter ('fltr')"%uri.scheme)
    query = urllib.parse.parse_qs(uri.query)
    for k in query: query[k] = query[k][-1]
    path = uri.path.strip('/').split('/')
    fclass, fsubclass = path[0], path[1] if len(path)>1 else None
    if fclass=="moving":
        if fsubclass in ("mean", "average"):
            return MovingMeanFilter(**query)
        elif fsubclass=="median":
            return MovingMedianFilter(**query)
        else:
            raise ValueError("Unknown or unspecified MovingWindowFilter subclass (%s)"%fsubclass)
    elif fclass=="exponential":
        if fsubclass=="single":
            return SingleExponentialFilter(**query)
        elif fsubclass=="double":
            return DoubleExponentialFilter(**query)
        elif fsubclass=="desp":
            return DESPFilter(**query)
        else:
            raise ValueError("Unknown or unspecified ExponentialFilter subclass (%s)"%fsubclass)
    elif fclass=="kalman":
        if fsubclass in ("constant", "p"):
            return ConstantValueKalmanFilter(**query)
        elif fsubclass in ("derivative", "derivate", "pv"):
            return DerivativeBasedKalmanFilter(**query)
        else:
            raise ValueError("Unknown or unspecified KalmanFilter subclass (%s)"%fsubclass)
    elif fclass in ("oneeuro", "1€"):
        if fsubclass is None:
            return OneEuroFilter(**query)
        else:
            raise ValueError("Unknown OneEuroFilter subclass (%s)"%fsubclass)
    raise ValueError("Unknown or unspecified filter class (%s)"%fclass)

if __name__=="__main__":
    import traceback
    tests = [
        "fltr:/moving/mean?winsize=5", "fltr:/moving/average",
        "/moving/median",
        "exponential/single?alpha=9.0",
        "exponential/double?alpha=9.0&gamma=8.0",
        "kalman/constant?x=3.0",
        "kalman/derivative?v=3.0",
        "oneeuro?frequency=60&cutoff=40",
        ]
    for uri in tests:
        try:
            flter = createFilter(uri)
            print(uri.ljust(50), flter)
        except:
            print('-'*80)
            print(uri)
            print()
            traceback.print_exc()
            print('-'*80)
