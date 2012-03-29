# -*- coding: utf-8 -*-
#
# boing/nodes/encoding.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import datetime
import io

from PyQt4 import QtCore

import boing.net.osc as osc
import boing.net.slip as slip

from boing.core.MappingEconomy import HierarchicalProducer, HierarchicalConsumer

class LogFile(QtCore.QObject, HierarchicalConsumer):

    def __init__(self, outputdevice, raw=False, parent=None):
        QtCore.QObject.__init__(self, parent)
        HierarchicalConsumer.__init__(self, request="osc")
        self.__out = outputdevice
        self.raw = raw
        self.cnt = 0 # for statistics...
        self.t0 = datetime.datetime.now()

    def __del__(self):
        self.__out.close()

    def file(self):
        return self.__out

    def logData(self, data, timetag=None):
        if timetag is None: timetag = datetime.datetime.now()
        packet = osc.EncodedPacket(data)
        if not self.raw:
            packet = osc.Bundle(timetag, (packet,))
        self.__out.write(slip.encode(packet.encode()))
        self.__out.flush()
        self.cnt = self.cnt+1
 
    def _consume(self, products, producer):
        for p in products:
            osc = p.get("osc")
            if osc: self.logData(osc.encode())

# -----------------------------------------------------------------

class LogPlayer(HierarchicalProducer):
    """
    TODO: should support partial decoding, i.e. decode only the bundle
    wrapper to get the timestamp
    """
    started = QtCore.pyqtSignal()
    stopped = QtCore.pyqtSignal()
    
    def __init__(self, fd, loop=False, speed=1.0, parent=None):
        HierarchicalProducer.__init__(self, parent)
        self.__timer = QtCore.QTimer(timeout=self.__proceed)
        self.__timer.setSingleShot(True)
        self.__fd = fd
        self._slipbuffer = None
        self._packets = collections.deque()
        self._running = False
        self.speed = speed
        self.looping = loop
        self.playcnt = 0
        """Time when the next packet should be sent."""
        self.__next = None
        self._addTag("osc", {"osc": osc.Packet()})
        self._addTag("timetag", {"timetag": datetime.datetime.now()})

    def start(self):
        if self.__fd.isOpen() and not self._running:
            self._running = True
            self.playcnt = self.playcnt+1
            self.started.emit()
            self._parseSendOutAndWait()
        
    def stop(self):
        self.__timer.stop()
        if self.__fd.isOpen(): self.__fd.seek(0)
        self._slipbuffer = None
        self._packets.clear()
        self.__next = None
        self._running = False
        self.stopped.emit()

    def isPlaying(self):
        return self._running

    def setSpeed(self, speed):
        self.speed = speed

    def _parseSendOutAndWait(self):
        while self.__parse() and len(self._packets)<2: pass
        if not self.__fd.isOpen():
            self.stop()
            return 
        if self._packets:
            # Send out the first packet
            first = self._packets.popleft()
            self.__sendOut(first.elements)
        if not self._packets:
            # Log is finished 
            self.stop()
            if self.looping: 
                self.__timer.start(1000)
            else:
                # FIXME: Handle how to notify that a log is terminated
                # self.__sendOut(None)
                pass
        else:
            # Read the next bundle and wait 
            now = datetime.datetime.now()
            delta = self._packets[0].timetag - first.timetag
            if self.__next is not None: delta = delta - (now - self.__next)
            self.__next = now + delta
            seconds = \
                delta.days*24*3600 + \
                delta.seconds + \
                delta.microseconds*1e-6
            interval = seconds*1000/self.speed
            self.__timer.start(interval if interval>0 else 0)

    def __parse(self):
        rvalue = False
        if self.__fd.isOpen(): 
            encoded = self.__fd.read()
            if encoded: 
                packets, self._slipbuffer = slip.decode(encoded, self._slipbuffer)
                self._packets.extend(map(osc.decode, packets))
                rvalue = True
        return rvalue

    def __sendOut(self, packets):
        if self._tag("osc"):
            for packet in packets:
                if isinstance(packet, osc.Bundle):
                    packet.timetag = self.__next if self.__next is not None \
                        else datetime.datetime.now()
                product = {"osc": packet}
                if self._tag("timetag"):
                    product["timetag"] = self.__next if self.__next is not None \
                        else datetime.datetime.now()
                self._postProduct(product)

    def __proceed(self):
        if self.isPlaying():
            self._parseSendOutAndWait()
        else:
            self.start()
