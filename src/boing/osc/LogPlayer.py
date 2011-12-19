# -*- coding: utf-8 -*-
#
# boing/osc/LogPlayer.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import weakref

from PyQt4.QtCore import pyqtSignal

from boing import osc, slip
from boing.eventloop.EventLoop import EventLoop
from boing.eventloop.ProducerConsumer import Producer

class LogPlayer(Producer):
    """
    TODO: should support partial decoding, i.e. decode only the bundle
    wrapper to get the timestamp
    """
    started = pyqtSignal()
    stopped = pyqtSignal()
    
    def __init__(self, fd, parent=None):
        Producer.__init__(self, parent)
        self.__tid = None
        self.__fd = fd
        self._slipbuffer = None
        self._packets = []
        self._running = False
        self.speed = 1.0
        self.looping = False
        self.playcnt = 0

    def start(self, looping=False):
        if self.__fd.isOpen() and not self._running:
            self._slipbuffer = None
            self._running = True
            self.looping = looping
            self.playcnt = self.playcnt+1
            self.started.emit()
            self._parseSendOutAndWait()
        
    def stop(self):
        self._running = False
        self._slipbuffer = None
        if self.__fd.isOpen(): self.__fd.seek(0)
        if self.__tid is not None:
            EventLoop.cancel_timer(self.__tid)
            self.__tid = None
        self.stopped.emit()

    def isPlaying(self):
        return self._running

    def _parseSendOutAndWait(self):
        while self.__parse() and len(self._packets)<2: pass
        if not self.__fd.isOpen():
            self.stop()
            return 
        if self._packets:
            # Send out the first packet
            first = self._packets.pop(0)          
            self.__sendOut(first.elements)
        if not self._packets:
            # Log is finished 
            self.__sendOut(None)
            self.stop()
            if self.looping:
                self.__tid = EventLoop.after(1.0, LogPlayer.__restart,
                                             weakref.ref(self))
        else:
            # Read the next bundle and wait 
            second = self._packets[0]
            delta = second.timetag - first.timetag
            seconds = delta.days*24*3600 + delta.seconds + delta.microseconds*1e-6
            self.__tid = EventLoop.after(seconds/self.speed, self.__proceed,
                                         weakref.ref(self))

    def __parse(self):
        if self.__fd.isOpen(): 
            encoded = self.__fd.read()
            if encoded: 
                packets, self._slipbuffer = slip.decode(encoded, self._slipbuffer)
                self._packets.extend(map(osc.decode, packets))
                return True
        return False

    def __sendOut(self, packets):
        if packets:
            for packet in packets:
                self._postProduct({"osc":packet, "data":packet.encode()})
        else: 
            self._postProduct({"data":bytes()})

    @staticmethod
    def __proceed(tid, ref):
        player = ref()
        if player is not None: player._parseSendOutAndWait()
        else: EventLoop.cancel_timer(tid)

    @staticmethod
    def __restart(tid, ref):
        player = ref()
        if player is not None: player.start(True)
        else: EventLoop.cancel_timer(tid)
