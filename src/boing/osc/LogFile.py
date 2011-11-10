# -*- coding: utf-8 -*-
#
# boing/osc/LogFile.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import datetime

from boing import osc, slip
from boing.eventloop.ProducerConsumer import Consumer
from boing.utils.ExtensibleStruct import ExtensibleStruct

class LogFile(Consumer):

    def __init__(self, outputdevice, raw=False, parent=None):
        Consumer.__init__(self, parent=parent)
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
            if isinstance(p, ExtensibleStruct): 
                data = p.get("data")
                if data: self.logData(data)
                else:
                    packet = p.get("osc")
                    if packet is not None: self.logPacket(packet)


