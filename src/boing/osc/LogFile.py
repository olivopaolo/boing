# -*- coding: utf-8 -*-
#
# boing/osc/LogFile.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import datetime

from PyQt4.QtCore import QObject

from boing import osc, slip
from boing.eventloop.ProducerConsumer import Consumer

class LogFile(QObject, Consumer):

    def __init__(self, outputdevice, raw=False, parent=None):
        QObject.__init__(self, parent)
        Consumer.__init__(self)
        self.__out = outputdevice
        self.raw = raw
        self.cnt = 0 # for statistics...
        self.t0 = datetime.datetime.now()

    def __del__(self):
        self.close()

    def file(self):
        return self.__out

    def close(self):
        self.__out.close()        

    def logData(self, data, timetag=None):
        if timetag is None: timetag = datetime.datetime.now()
        packet = osc.EncodedPacket(data)
        if not self.raw:
            packet = osc.Bundle(timetag, (packet,))
        self.__out.write(slip.encode(packet.encode()))
        self.__out.flush()
        self.cnt = self.cnt+1
    
    def logPacket(self, packet):
        self.logData(packet.encode())
 
    def _consume(self, products, producer):
        for p in products:
            if isinstance(p, collections.Mapping): 
                data = p.get("data")
                if data: self.logData(data)
                elif "osc" in p: self.logPacket(p["osc"])


