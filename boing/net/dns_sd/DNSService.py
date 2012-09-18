# -*- coding: utf-8 -*-
#
# boing/net/dns_sd/DNSService.py -
#
# Authors: 
#  Nicolas Roussel (nicolas.roussel@inria.fr)
#  Paolo Olivo (paolo.olivo@inria.fr)  
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import logging
import struct
import traceback

from PyQt4 import QtCore

from boing.net.dns_sd.dns_sd import *

# -------------------------------------------------------------------------------

def _constructFullName(name, regtype, domain):
    tmp = create_string_buffer(kDNSServiceMaxDomainName)
    global_lock.acquire()
    result = dns_sd.DNSServiceConstructFullName(tmp, 
                                                name.encode("utf-8"), 
                                                regtype.encode("utf-8"), 
                                                domain.encode("utf-8"))
    global_lock.release()
    if result==0:
        value = tmp.value.decode("utf-8")
        if value[-1]!='.': value += '.'
        return value
    return ""

def _parseSRVdata(data, len):
    rdata = cast(data, POINTER(c_char))
    priority, weight, port = struct.unpack('!HHH', rdata[:6])
    i, targets = 6, []
    while i<len:
        size = ord(rdata[i])
        if size<1: break
        i = i+1
        targets.append(rdata[i:i+size])
        i = i+size
    return {
        "priority":priority,
        "weight":weight,
        "port":port,
        "target":".".join(i.decode() for i in targets),
        }

def _parseTXTdata(rec, length):
    txtchars = cast(rec, POINTER(c_char))
    record = ''.join(txtchars[i].decode() for i in range(length))
    result = {}
    while record:
        kvlen = ord(record[0])
        kv = record[1:kvlen+1].split('=', 1)
        if len(kv)==1 or not kv[1]:
            k, v = kv[0], None
        else :
            k, v = kv
        if k: result[k] = v
        record = record[kvlen+1:]
    return result

# -------------------------------------------------------------------------------

class DNSService(object):

    def __init__(self, name, regtype, domain, 
                 interface=kDNSServiceInterfaceIndexAny):
        self.logger = logging.getLogger("DNSService.%d"%id(self))
        self.interface = interface
        self.interfaceName = if_indextoname(interface)
        # service type
        self.type = regtype.decode("utf-8")
        if self.type[-1]=='.': self.type = self.type[:-1]
        if not self.type \
           or len(self.type)<6 \
           or self.type[-4:] not in ("_tcp","_udp"):
            raise ValueError("Bad service type")
        # domain
        if not domain: raise ValueError("Bad domain name")
        self.domain = domain.decode("utf-8")
        if self.domain[-1]!='.': self.domain = self.domain+'.'
        # name
        if name is None: name = ""
        else: self.name = name.decode("utf-8")
        self.__parseRecord = DNSServiceQueryRecordReply(self.__parseRecord)
        self.__txtfd = self.__txtref = None
        self.__srvfd = self.__srvref = None
        """ When True, __listeners are invoked. """
        self.__txtnotify = self.__srvnotify = False
        self.info = {}
        self.__lock = global_lock 
        self.__listeners = []

    def __del__(self):
        if self.__txtref:
            self.__txtfd.setEnabled(False)
            self.__lock.acquire()
            dns_sd.DNSServiceRefDeallocate(self.__txtref)
            self.__lock.release()
        
    def __str__(self):
        # <boing.dns_sd.DNSService.DNSService object at 0x2373fb0>
        return "<%s.%s object at 0x%x (%s)>"%(__name__,
                                              self.__class__.__name__,id(self),
                                              self.fullname())

    def __parseRecord(self, sdRef, flags, interface, errorCode,
                      fullname, rrtype, rrclass, rdlen, rdata, ttl, context):
        """Parse service response."""
        if interface not in self.info: 
            self.info[interface] = {"srv":{}, "txt":{}}
        if rrtype==kDNSServiceType_SRV:
            srvrec = _parseSRVdata(rdata, rdlen)
            #print "SRV %s ttl=%d %s"%(self.interface,ttl,srvrec)
            self.info[interface]["srv"] = srvrec
            self.__srvnotify = True
            # After the response has been read it is possible to
            # deallocate the resource
            self.__srvfd.setEnabled(False)
            self.__lock.acquire()
            dns_sd.DNSServiceRefDeallocate(self.__srvref)
            self.__lock.release()
            self.__srvref = None
        elif rrtype==kDNSServiceType_TXT:
            txtrec = _parseTXTdata(rdata,rdlen)
            # Commented because I don't understand the meaning
            # if ttl==0: # goodbye message
            #    txt = self.info[interface]["txt"]
            #    if txt==txtrec: self.info[interface]["txt"] = {}
            #else:
            self.info[interface]["txt"] = txtrec
            self.__txtnotify = True
        else:
            self.logger.warning("__parseRecord: ??? (%s) ttl=%d"%(rrtype,ttl))
            
    def __srvreadable(self, did):
        if not self.__srvref: return
        self.__lock.acquire()
        result = dns_sd.DNSServiceProcessResult(self.__srvref)
        self.__lock.release()
        if result!=kDNSServiceErr_NoError:
            self.logger.warning("DNSServiceProcessResult failed (__srvreadable)")
        if self.__srvnotify:
            self.__srvnotify = False
            for (callback, args, kwargs) in self.__listeners:
                if not isinstance(callback, collections.Callable): continue
                try:
                    callback("resolved", self, *args, **kwargs)
                except:
                    traceback.print_exc()

    def __txtreadable(self, did):
        if not self.__txtref: return
        self.__lock.acquire()
        result = dns_sd.DNSServiceProcessResult(self.__txtref)
        self.__lock.release()
        if result!=kDNSServiceErr_NoError:
            self.logger.warning("DNSServiceProcessResult failed (__txtreadable)")
        if self.__txtnotify:
            self.__txtnotify = False
            for (callback, args, kwargs) in self.__listeners:
                if not isinstance(callback, collections.Callable): continue
                try:
                    callback("txtupdate", self, *args, **kwargs)
                except:
                    traceback.print_exc()

    def addListener(self, callback, *args, **kwargs):
        self.__listeners.append((callback,args,kwargs))

    def fullname(self):
        return _constructFullName(self.name, self.type, self.domain)
        # alternate version...
        result = ""
        s = self.name.encode("utf-8")
        if s:
            for c in s:
                if c<=' ':
                    result = result + '\\%03d'%ord(c)
                elif c in ('.','\\'):
                    result = result + '\\' + c
                else:
                    result = result + c
            result = result+"."
        t = self.type.encode("utf-8")
        if t[-1]!='.': t = t+'.'
        d = self.domain.encode("utf-8")
        if d[-1]!='.': d = d+'.'
        result = result+t+d
        return result

    def key(self):
        return "%s:%s"%(self.interface, self.fullname())
        # alternate version...
        return (self.fullname(), self.interface)

    def resolve(self, clearcache=True):
        if self.__srvref: return
        if clearcache:
            for key in self.info.keys(): 
                self.info[key]["srv"] = {}
        flags, context = 0, None
        self.__srvref = DNSServiceRef()
        self.__lock.acquire()
        err = dns_sd.DNSServiceQueryRecord(byref(self.__srvref), 
                                           flags, self.interface, 
                                           self.fullname().encode("utf-8"),
                                           kDNSServiceType_SRV, 
                                           kDNSServiceClass_IN,
                                           self.__parseRecord, 
                                           context)
        self.__lock.release()
        if err!=kDNSServiceErr_NoError:            
            self.logger.warning("DNSServiceQueryRecord failed (resolve, SRV)")
        else:
            self.__lock.acquire()
            obj = dns_sd.DNSServiceRefSockFD(self.__srvref)
            self.__lock.release()
            self.__srvfd = QtCore.QSocketNotifier(obj, QtCore.QSocketNotifier.Read,
                                                  activated=self.__srvreadable)
                
    def queryTXTrecord(self, clearcache=True):
        if self.__txtref: return
        if clearcache:
            for key in self.info.keys(): 
                self.info[key]["txt"] = {}
        flags, context = 0, None
        self.__txtref = DNSServiceRef()
        self.__lock.acquire()
        err = dns_sd.DNSServiceQueryRecord(byref(self.__txtref), 
                                           flags, self.interface, 
                                           self.fullname().encode("utf-8"),
                                           kDNSServiceType_TXT, 
                                           kDNSServiceClass_IN,
                                           self.__parseRecord,
                                           context)
        self.__lock.release()
        if err!=kDNSServiceErr_NoError:
            self.logger.warning("DNSServiceQueryRecord failed (resolve, TXT)")
        else:
            self.__lock.acquire()
            obj = dns_sd.DNSServiceRefSockFD(self.__txtref)
            self.__lock.release()
            self.__txtfd = QtCore.QSocketNotifier(obj, QtCore.QSocketNotifier.Read,
                                                  activated=self.__txtreadable)
