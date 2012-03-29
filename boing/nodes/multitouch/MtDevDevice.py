#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# boing/nodes/multitouch/MtDevDevice.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import copy
import datetime
import os
import ctypes

from PyQt4 import QtCore

import boing.utils as utils
import boing.utils.fileutils as fileutils
from boing.core.StateMachine import StateNode

'''
The mtdev library transforms all variants of kernel MT events to the
slotted type B protocol. The events put into mtdev may be from any MT
device, specifically type A without contact tracking, type A with
contact tracking, or type B with contact tracking. See the kernel
documentation for further details.
'''

# --- time.h bindings ---
class timeval(ctypes.Structure):
    _fields_ = [
        ('tv_sec', ctypes.c_ulong),
        ('tv_usec', ctypes.c_ulong)
    ]

# --- linux/input.h bindings ---
""" Event types """
EV_ABS        = 0x03
EV_SYN        = 0x00
EV_KEY        = 0x01
EV_REL        = 0x02
EV_ABS        = 0x03
EV_MSC        = 0x04
EV_SW         = 0x05
EV_LED        = 0x11
EV_SND        = 0x12
EV_REP        = 0x14
EV_FF         = 0x15
EV_PWR        = 0x16
EV_FF_STATUS  = 0x17
EV_MAX	      = 0x1f
EV_CNT	      =	EV_MAX+1

""" Synchronization events """
SYN_REPORT    =	0
SYN_CONFIG    =	1
SYN_MT_REPORT =	2

class input_event(ctypes.Structure):
    _fields_ = [
        ('time', timeval),
        ('type', ctypes.c_ushort),
        ('code', ctypes.c_ushort),
        ('value', ctypes.c_int)
    ]

class input_absinfo(ctypes.Structure):
    _fields_ = [
        ('value', ctypes.c_int),
        ('minimum', ctypes.c_int),
        ('maximum', ctypes.c_int),
        ('fuzz', ctypes.c_int),
        ('flat', ctypes.c_int),
        ('resolution', ctypes.c_int)
    ]

# --- mtdev.h bindings ---
# load library
libmtdev = ctypes.cdll.LoadLibrary('libmtdev.so.1')

ABS_MT_TOUCH_MAJOR	 = 0x30	 # Major axis of touching ellipse
ABS_MT_TOUCH_MINOR	 = 0x31	 # Minor axis (omit if circular)
ABS_MT_WIDTH_MAJOR	 = 0x32	 # Major axis of approaching ellipse
ABS_MT_WIDTH_MINOR	 = 0x33	 # Minor axis (omit if circular)
ABS_MT_ORIENTATION	 = 0x34	 # Ellipse orientation
ABS_MT_POSITION_X	 = 0x35	 # Center X ellipse position
ABS_MT_POSITION_Y	 = 0x36	 # Center Y ellipse position
ABS_MT_TOOL_TYPE	 = 0x37	 # Type of touching device
ABS_MT_BLOB_ID		 = 0x38	 # Group a set of packets as a blob
ABS_MT_TRACKING_ID	 = 0x39	 # Unique ID of initiated contact
""" includes available in 2.6.33 """
ABS_MT_PRESSURE		 = 0x3a	 # Pressure on contact area
""" includes available in 2.6.36 """
ABS_MT_SLOT		 = 0x2f	 # MT slot being modified
""" includes available in 2.6.38 """
ABS_MT_DISTANCE		 = 0x3b	 # Contact hover distance

MT_ABS_SIZE              = 11

event_name = {
    ABS_MT_SLOT: "ABS_MT_SLOT",
    ABS_MT_TOUCH_MAJOR: "ABS_MT_TOUCH_MAJOR",
    ABS_MT_TOUCH_MINOR: "ABS_MT_TOUCH_MINOR",
    ABS_MT_WIDTH_MAJOR: "ABS_MT_WIDTH_MAJOR",
    ABS_MT_WIDTH_MINOR: "ABS_MT_WIDTH_MINOR",
    ABS_MT_ORIENTATION: "ABS_MT_ORIENTATION",
    ABS_MT_POSITION_X: "ABS_MT_POSITION_X",
    ABS_MT_POSITION_Y: "ABS_MT_POSITION_Y",
    ABS_MT_TOOL_TYPE: "ABS_MT_TOOL_TYPE",
    ABS_MT_BLOB_ID: "ABS_MT_BLOB_ID",
    ABS_MT_TRACKING_ID: "ABS_MT_TRACKING_ID",
    ABS_MT_PRESSURE: "ABS_MT_PRESSURE",
    ABS_MT_DISTANCE: "ABS_MT_DISTANCE"
}

class mtdev_caps(ctypes.Structure):
    _fields_ = [
        ('has_mtdata', ctypes.c_int),
        ('has_slot', ctypes.c_int),
        ('has_abs', ctypes.c_int * MT_ABS_SIZE),
        ('slot', input_absinfo),
        ('abs', input_absinfo * MT_ABS_SIZE)
    ]

class mtdev(ctypes.Structure):
    _fields_ = [
        ('caps', mtdev_caps),
        ('state', ctypes.c_void_p)
    ]

"""
 * mtdev_open - open an mtdev converter
 * @dev: the mtdev to open
 * @fd: file descriptor of the kernel device
 *
 * Initialize the mtdev structure and configure it by reading
 * the protocol capabilities through the file descriptor.
 *
 * Returns zero on success, negative error number otherwise.
 *
 * This call combines the plumbing functions mtdev_init() and
 * mtdev_configure().
"""
mtdev_open = libmtdev.mtdev_open
mtdev_open.argtypes = [ctypes.POINTER(mtdev), ctypes.c_int]

"""
 * mtdev_has_mt_event - check for event type
 * @dev: the mtdev in use
 * @code: the ABS_MT code to look for
 *
 * Returns true if the given event code is present.
"""
mtdev_has_mt_event = libmtdev.mtdev_has_mt_event
mtdev_has_mt_event.argtypes = [ctypes.POINTER(mtdev), ctypes.c_int]

"""
 * mtdev_get_abs_<property> - get abs event property
 * @dev: the mtdev in use
 * @code: the ABS_MT code to look for
 *
 * Returns NULL if code is not a valid ABS_MT code.
"""
mtdev_get_abs_minimum = libmtdev.mtdev_get_abs_minimum
mtdev_get_abs_minimum.argtypes = [ctypes.POINTER(mtdev), ctypes.c_int]

mtdev_get_abs_maximum = libmtdev.mtdev_get_abs_maximum
mtdev_get_abs_maximum.argtypes = [ctypes.POINTER(mtdev), ctypes.c_int]

mtdev_get_abs_fuzz = libmtdev.mtdev_get_abs_fuzz
mtdev_get_abs_fuzz.argtypes = [ctypes.POINTER(mtdev), ctypes.c_int]

mtdev_get_abs_resolution = libmtdev.mtdev_get_abs_resolution
mtdev_get_abs_resolution.argtypes = [ctypes.POINTER(mtdev), ctypes.c_int]

"""
 * mtdev_idle - check state of kernel device
 * @dev: the mtdev in use
 * @fd: file descriptor of the kernel device
 * @ms: number of milliseconds to wait for activity
 *
 * Returns true if the device is idle, i.e., there are no fetched
 * events in the pipe and there is nothing to fetch from the device.
"""
mtdev_idle = libmtdev.mtdev_idle
mtdev_idle.argtypes = [ctypes.POINTER(mtdev), ctypes.c_int, ctypes.c_int]

"""
 * mtdev_get - get processed events from mtdev
 * @dev: the mtdev in use
 * @fd: file descriptor of the kernel device
 * @ev: array of input events to fill
 * @ev_max: maximum number of events to read
 *
 * Get a processed event from mtdev. The events appear as if they came
 * from a type B device emitting MT slot events.
 *
 * The read operations involved behave as dictated by the file
 * descriptor; if O_NONBLOCK is not set, mtdev_get() will block until
 * the specified number of processed events are available.
 *
 * On success, returns the number of events read. Otherwise,
 * a standard negative error number is returned.
 *
 * This call combines the plumbing functions mtdev_fetch_event(),
 * mtdev_put_event() and mtdev_get_event().
"""
mtdev_get = libmtdev.mtdev_get
mtdev_get.argtypes = [ctypes.POINTER(mtdev), ctypes.c_int, 
                      ctypes.POINTER(input_event), ctypes.c_int]

"""
 * mtdev_close - close the mtdev converter
 * @dev: the mtdev to close
 *
 * Deallocates all memory associated with mtdev, and clears the mtdev
 * structure.
"""
mtdev_close = libmtdev.mtdev_close
mtdev_close.argtypes = [ctypes.POINTER(mtdev)]

# -------------------------------------------------------------------

class MtDevDevice(StateNode):

    class Slot(object):
        """A slot describes the caracteristics of a single touch interaction."""
        def __init__(self):
            self.data = dict()
            self.id = -1
            self.modified = set()

    class AbsInfo(object):
        def __init__(self, minimum, maximum, resolution):
            self.min = minimum
            self.max = maximum
            self.res = resolution
        def __str__(self):
            return "(min=%i, max=%i, res=%i)"%(self.min, self.max, self.res)
    
    def __init__(self, filename, parent=None):
        #FIXME: set productoffer
        StateNode.__init__(self, parent=parent)
        self.__filename = filename
        # Open device node        
        self.__file = fileutils.CommunicationDevice(os.fdopen(
                os.open(filename, os.O_NONBLOCK | os.O_RDONLY),
                "rb", 0))
        # Init mtdev device
        self.__device = mtdev()
        if mtdev_open(ctypes.byref(self.__device), self.__file.fd().fileno()):
            self.__file.close()
            raise Exception('Unable to open device')
        # Init slot data
        """Slot default values."""
        self.__template = MtDevDevice.Slot()        
        self._eventinfo = {}
        """Slots describes a touch point."""
        self.__slots = []
        """Current updating slot."""        
        self.__cs = 0
        """Frame id."""
        self.__fseq = 0
        self._update = False
        if mtdev_has_mt_event(self.__device, ABS_MT_SLOT):
            self.__slots = [None] * mtdev_get_abs_maximum(
                ctypes.byref(self.__device),
                ABS_MT_SLOT)
        else:
            # In this case the kernel does not provide Type B events for the
            # requested device and it is libmtdev to emulate slots and tracking
            # id. So it is necessary to use a default value.
            self.DEFAULT_SLOT_NUM = 10
            self.__slots = [None] * self.DEFAULT_SLOT_NUM
        # Set default tracking id as -1, which means no tracking.
        self.__template.data[ABS_MT_TRACKING_ID] = -1
        # Init properties
        for code in (ABS_MT_SLOT,
                     ABS_MT_TOUCH_MAJOR, ABS_MT_TOUCH_MINOR, 
                     ABS_MT_WIDTH_MAJOR, ABS_MT_WIDTH_MINOR,
                     ABS_MT_ORIENTATION,
                     ABS_MT_POSITION_X, ABS_MT_POSITION_Y,
                     ABS_MT_TOOL_TYPE, ABS_MT_BLOB_ID,
                     ABS_MT_PRESSURE, ABS_MT_DISTANCE):            
            self._checkHasEvent(code)
        # Setup initial state
        if ABS_MT_POSITION_X in self._eventinfo \
          and ABS_MT_POSITION_Y in self._eventinfo:
            # set position ranges & resolution
            self._state.contacts.pos_range = (
                (self._eventinfo[ABS_MT_POSITION_X].min, 
                 self._eventinfo[ABS_MT_POSITION_X].max), 
                (self._eventinfo[ABS_MT_POSITION_Y].min, 
                 self._eventinfo[ABS_MT_POSITION_Y].max))
            # value is multiplied per 0.001 because resolution for main 
            # axes (ABS_X, ABS_Y, ABS_Z) is reported in units per millimeter 
            # (units/mm) while boing resolution is units/m
            res = (self._eventinfo[ABS_MT_POSITION_X].res*0.001, 
                   self._eventinfo[ABS_MT_POSITION_Y].res*0.001)
            if res[0] and res[1]: self._state.contacts["pos_res"] = res
        '''if ABS_MT_TOUCH_MAJOR in self._eventinfo  \
          and ABS_MT_TOUCH_MINOR in self._eventinfo:
            # set position ranges & resolution
            majtouch_absinfo = self._eventinfo[ABS_MT_TOUCH_MAJOR]
            mintouch_absinfo = self._eventinfo[ABS_MT_TOUCH_MINOR]
            #bb = ExtensibleEvent()
            #bb.size_range = ((majtouch_absinfo.min, majtouch_absinfo.max),
            #                 (mintouch_absinfo.min, mintouch_absinfo.max))
            # value is multiplied per 0.001 because resolution for main 
            # axes (ABS_X, ABS_Y, ABS_Z) is reported in units per millimeter
            # (units/mm) while EE resolution is units/m
            #res = (float(majtouch_absinfo.res)* 0.001, 
            #       float(mintouch_absinfo.res)* 0.001)
            #if res[0]!=0 and res[1]!=0: bb.size_res = res
            #self.state.contacts["boundingbox"] = bb'''
        self.__halfpi = 1.5707963267948966
        # Init timer
        self.__timer = QtCore.QTimer()
        self.__timer.timeout.connect(self._fetchEvent, QtCore.Qt.QueuedConnection)
        self.__timer.setSingleShot(True)
        self.__timer.start(0)

    def __del__(self):
        if self.__file.isOpen():
            if self.__device is not None: 
                mtdev_close(ctypes.byref(self.__device))
            self.__file.close()
        StateNode.__del__(self)

    def _fetchEvent(self):
        ev = input_event()
        if mtdev_get(ctypes.byref(self.__device), 
                     self.__file.fd().fileno(), 
                     ctypes.byref(ev), 1):
            self._processEvent(ev)
        self.__timer.start(0)

    def _processEvent(self, ev):
        """Process single mtdev event."""
        #print("%d %d %d"%(ev.type, ev.code, ev.value))
        if ev.type==EV_ABS:
            if ev.code is ABS_MT_SLOT: self.__cs = ev.value
            elif self.__cs<len(self.__slots):
                if self.__slots[self.__cs] is None:
                    # create a new slot from template
                    self.__slots[self.__cs] = copy.deepcopy(self.__template)
                self.__slots[self.__cs].modified.add(ev.code)
                self.__slots[self.__cs].data[ev.code] = ev.value
                self._update = True
                # since some values are omitted if circular blob
                if ev.code==ABS_MT_TOUCH_MAJOR:
                    self.__slots[self.__cs].data[ABS_MT_TOUCH_MINOR] = ev.value
                elif ev.code==ABS_MT_WIDTH_MAJOR:
                    self.__slots[self.__cs].data[ABS_MT_WIDTH_MINOR] = ev.value
        elif ev.type==EV_SYN and ev.value==SYN_REPORT:
            #print("SYNC", end="")
            if self.__fseq and self._update: self._sendOut()
            self.__fseq += 1

    def _sendOut(self):
        """Composes received events and notifies observers."""
        self._update = False
        diff = utils.quickdict()
        for sl in self.__slots:
            if sl is not None and sl.modified:
                track_id = sl.data[ABS_MT_TRACKING_ID]
                if sl.id==track_id: # update
                    if track_id==-1: continue
                elif sl.id==-1: # touch press
                    sl.id = track_id
                elif track_id==-1: # touch release
                    diff.removed.contacts[str(sl.id)] = None
                    sl.id = -1
                    continue
                else: raise Exception("Slot changed ABS_MT_TRACKING_ID")
                track_id = str(track_id)
                if ABS_MT_POSITION_X in sl.modified  \
                  or ABS_MT_POSITION_Y in sl.modified:
                    # Set position                    
                    diff.updated.contacts[track_id].pos = (
                        sl.data[ABS_MT_POSITION_X], 
                        sl.data[ABS_MT_POSITION_Y])
                    diff.updated.contacts[track_id].rel_pos = (
                        sl.data[ABS_MT_POSITION_X] \
                            / self._eventinfo[ABS_MT_POSITION_X].max,
                        sl.data[ABS_MT_POSITION_Y] \
                            / self._eventinfo[ABS_MT_POSITION_Y].max)
                if ABS_MT_TOUCH_MAJOR in sl.modified  \
                  or ABS_MT_TOUCH_MINOR in sl.modified:
                    major = sl.data[ABS_MT_TOUCH_MAJOR] \
                            / self._eventinfo[ABS_MT_TOUCH_MAJOR].max 
                    minor = sl.data[ABS_MT_TOUCH_MINOR] \
                            / self._eventinfo[ABS_MT_TOUCH_MAJOR].max 
                    angle = sl.data.get(ABS_MT_ORIENTATION, 0.0)
                    bb = utils.quickdict()
                    bb.rel_size = (major, minor)
                    bb.si_angle = (self.__halfpi if angle==0 else 0, )
                    diff.updated.contacts[track_id].boundingbox = bb
                sl.modified.clear()
        additional = {"timetag": datetime.datetime.now(),
                      "source": "mtdev://%s"%self.__filename}
        self.applyDiff(diff, additional)

    def _checkHasEvent(self, code):
         if mtdev_has_mt_event(ctypes.byref(self.__device), code):
             self.__template.data[code] = mtdev_get_abs_minimum(
                 ctypes.byref(self.__device), code)
             self._eventinfo[code] = self.AbsInfo(
                 mtdev_get_abs_minimum(ctypes.byref(self.__device), code),
                 mtdev_get_abs_maximum(ctypes.byref(self.__device), code),
                 mtdev_get_abs_resolution(ctypes.byref(self.__device), code))
    
    def printSupportedEvents(self):
        """Prints libmtdev device properties."""
        print("Supported mt events:")
        for k, v in self._eventinfo.items():
            print("-", event_name[k], v)
    
