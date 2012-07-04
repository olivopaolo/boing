# -*- coding: utf-8 -*-
#
# boing/filtering/filter/KalmanFilter.py -
#
# Authors: Paolo Olivo (paolo.olivo@inria.fr)
#          Nicolas Roussel (nicolas.roussel@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import numpy

class LinearKalmanFilter:

    """From http://greg.czerniak.info/node/5"""

    def __init__(self, _A, _B, _H, _x, _P, _Q, _R):
        # A is the state transition matrix, i.e. what you need to
        # multiply to last time's state to get the newest state
        self.A = _A
        # B is the control matrix
        self.B = _B
        # H is the observation matrix, i.e. what you need to multiply
        # the incoming measurement to convert it to a state
        self.H = _H
        # xhat is your initial prediction of the voltage, i.e. initial state estimate
        self.current_state_estimate = _x
        # P is your initial prediction of the covariance, initial covariance estimate
        self.current_prob_estimate = _P
        # Q is the process variance, i.e. estimated error in process
        self.Q = _Q
        # R is the measurement variance, i.e. estimated error in measurements
        self.R = _R

    def GetCurrentState(self):
        return self.current_state_estimate

    def Step(self, control_vector, measurement_vector):
        #---------------------------Prediction step-----------------------------
        tmp = self.A * self.current_state_estimate
        predicted_state_estimate = tmp + self.B * control_vector
        predicted_prob_estimate = (self.A * self.current_prob_estimate) * numpy.transpose(self.A) + self.Q
        #--------------------------Observation step-----------------------------
        innovation = self.H*measurement_vector - predicted_state_estimate
        innovation_covariance = self.H*predicted_prob_estimate*numpy.transpose(self.H) + self.R
        #-----------------------------Update step-------------------------------
        kalman_gain = predicted_prob_estimate * numpy.transpose(self.H) * numpy.linalg.inv(innovation_covariance)
        self.current_state_estimate = predicted_state_estimate + kalman_gain * innovation
        # We need the size of the matrix so we can make an identity matrix.
        size = self.current_prob_estimate.shape[0]
        # eye(n) = nxn identity matrix.
        self.current_prob_estimate = (numpy.eye(size)-kalman_gain*self.H)*predicted_prob_estimate

# -------------------------------------------------------------------------------------

class ConstantValueKalmanFilter(LinearKalmanFilter):

    def __init__(self,
                 x=None,
                 p=1.0,     # an arbitrary value because we don't know any better
                 q=0.00001, # a very small variance
                 r=0.1):    # a conservative estimate
        A = numpy.matrix([[1]]) # x is assumed to be constant
        B = numpy.matrix([[0]]) # no input in the model we can change to affect anything
        H = numpy.eye(1)        # we get the signal value directly, so just multiply by 1
        if x in (None, "None"):
            xhat = None
        else:
            xhat = numpy.matrix([[float(x)]])
        P = numpy.array([[float(p)]])
        Q = numpy.matrix([[float(q)]])
        R = numpy.matrix([[float(r)]])
        super().__init__(A,B,H,xhat,P,Q,R)
        self.ctrl_vector = numpy.matrix([[0]])
        self.__args = "x=%s&p=%s&q=%s&r=%s"%(x,p,q,r)

    def __call__(self, value, timestamp=None):
        if self.current_state_estimate is None:
            self.current_state_estimate = numpy.matrix([[value]])
            return self.current_state_estimate
        state = self.GetCurrentState()
        self.Step(self.ctrl_vector, numpy.matrix([[value]]))
        return state[0,0]

    def getURL(self):
        return "fltr:/kalman/constant?"+self.__args

    def __str__(self):
        return self.getURL()

class DerivativeBasedKalmanFilter(LinearKalmanFilter):

    def __init__(self,
                 x=0.0, v=0.0, freq=60,
                 p=1.0,     # an arbitrary value because we don't know any better
                 q=0.00001, # a very small variance
                 r=0.1):    # a conservative estimate
        A = numpy.matrix([[1.0, 1.0/float(freq)], [0.0, 1.0]])
        B = numpy.matrix([[0, 0], [0, 0]])
        H = numpy.eye(2)
        xhat = numpy.matrix([[float(x)], [float(v)]])
        P = numpy.eye(2)*float(p)
        Q = numpy.ones(2)*float(q)
        R = numpy.eye(2)*float(r)
        super().__init__(A,B,H,xhat,P,Q,R)
        self.freq = float(freq)
        self.prev_measurement = None
        self.ctrl_vector = numpy.matrix([[0.0], [0.0]])
        self.__args = "x=%s&v=%s&freq=%s&p=%s&q=%s&r=%s"%(x,v,freq,p,q,r)

    def __call__(self, value, timestamp=None):
        state = self.GetCurrentState()
        if self.prev_measurement is None:
            speed = 0.0
        else:
            speed = (value-self.prev_measurement)*self.freq
        self.Step(self.ctrl_vector, numpy.matrix([[value], [speed]]))
        self.prev_measurement = value
        return state[0,0]

    def getURL(self):
        return "fltr:/kalman/derivative?"+self.__args

    def __str__(self):
        return self.getURL()
