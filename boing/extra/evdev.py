# -*- coding: utf-8 -*-
#
# boing/extra/evdev.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from PyQt4 import QtCore
import evdev

from boing.core import Offer, QRequest, Producer, Consumer
from boing.utils import quickdict

eventtag = "linux_input_event"

class InBridge(Producer):

    def __init__(self, filepath, parent=None):
        super().__init__(Offer({eventtag: object()}), parent=parent)
        self.__device = evdev.InputDevice(filepath)
        self.__notifier = QtCore.QSocketNotifier(self.__device.fileno(),
                                                 QtCore.QSocketNotifier.Read,
                                                 activated=self.__read)

    def __del__(self):
        super().__del__()
        try:
            self.__notifier.setEnabled(False)
        except Exception: pass

    def __read(self):
        for event in self.__device.read():
            self._processEvent(event)

    def _processEvent(self, event):
        self.postProduct(dict(linux_input_event=event))


class OutBridge(Consumer):

    def __init__(self, events, name="boing.uinput",
                 vendor=1, product=1, version=0x1,
                 bustype=3, devnode="/dev/uinput",
                 parent=None):
        super().__init__(QRequest(eventtag), parent=parent)
        self.__device = evdev.UInput(events, name,
                                     vendor, product, version, bustype,
                                     devnode)
        print(self.__device)
        print(self.__device.capabilities(verbose=True))

    def _consume(self, products, producer):
        for product in products:
            event = product.get(eventtag)
            if event is not None:
                self.__device.write(event.type, event.code, event.value)
