# -*- coding: utf-8 -*-
#
# boing/dns_sd/DNSServiceAnnouncer.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import logging
import socket
import sys

from boing.dns_sd.dns_sd import *
from boing.eventloop.EventLoop import EventLoop

def dict2txtrec(d):
    result = ""
    for k,v in d.items():
        if not k: continue
        encoded = "%s=%s"%(k,v) if v else k
        result = "%s%c%s"%(result,len(encoded),encoded)
    return result.encode()


class DNSServiceAnnouncer(object):
   
    def __init__(self, name, regtype, port, 
                 txtrec={}, host=None, domain=None, 
                 interface=kDNSServiceInterfaceIndexAny,
                 callback=None):
        self.__register = DNSServiceRegisterReply(self.__register)
        self.__notify = False
        self.__type = None
        self.__name = None
        self.__domain = None
        self.__status = None
        self.__sdRef = DNSServiceRef()
        self.__callback = callback if callback is not None else lambda a: None
        self.__lock = global_lock
        if sys.platform=='win32' and port==0:
            logging.warning("win32 does not permit to publish services on port 0.")
        txtrec = dict2txtrec(txtrec)
        flags, context = 0, None
        self.__lock.acquire()
        result = dns_sd.DNSServiceRegister(byref(self.__sdRef),
                                           flags, interface,
                                           name.encode(), 
                                           regtype.encode(),
                                           None if domain is None else domain.encode(), 
                                           None if host is None else host.encode(), 
                                           socket.htons(port),
                                           len(txtrec), txtrec,
                                           self.__register,
                                           context)
        self.__lock.release()
        if result!=kDNSServiceErr_NoError:
            raise RuntimeError("DNSServiceRegister failed")
        self.__lock.acquire()
        obj = dns_sd.DNSServiceRefSockFD(self.__sdRef)
        self.__lock.release()
        self.__did = EventLoop.if_readable(obj, self.__readable)

    def __del__(self):
        EventLoop.cancel_fdhandler(self.__did)
        self.__lock.acquire()
        dns_sd.DNSServiceRefDeallocate(self.__sdRef)
        self.__lock.release()
        
    def __readable(self, did):   
        self.__lock.acquire()
        result = dns_sd.DNSServiceProcessResult(self.__sdRef)
        self.__lock.release()
        if result!=kDNSServiceErr_NoError:
            self.logger.warning("DNSServiceProcessResult failed (__readable)")
        # __register is not invoked everytime __readable is
        # invoked so it is necessary a variable to verifying it.
        if self.__notify:
            self.__notify = False
            if isinstance(self.__callback, collections.Callable): 
                self.__callback(self)

    def __register(self, sdRef, flags, errorcode, 
                   name, regtype, domain, context):
        self.__type = regtype.decode()
        self.__name = name.decode()
        self.__domain = domain.decode()
        if errorcode==kDNSServiceErr_NoError: 
            self.__status = "noerror"
        elif errorcode==kDNSServiceErr_NameConflict: 
            self.__status = "nameconflict"
        else: self.__status = "error"
        self.__notify = True
        
    def updatetxt(self, txtrec):
        txtrec = dict2txtrec(txtrec)
        flags, ttl = 0, 0
        self.__lock.acquire()
        dns_sd.DNSServiceUpdateRecord(self.__sdRef, None, flags, 
                                      len(txtrec), txtrec, ttl)
        self.__lock.release()

    def name(self):
        return self.__name

    def domain(self):
        return self.__domain

    def type(self):
        return self.__type

    def status(self):
        return self.__status

# ----------------------------------------------------------------

if __name__=="__main__":    

    def callback(announcer):
        print("Registered service:")
        print(" name: \"%s\""%announcer.name())
        print(" domain: \"%s\""%announcer.domain())
        print(" type: \"%s\""%announcer.type())
        print(" status:", announcer.status())

    s1 = DNSServiceAnnouncer("roussel","_test._tcp.",8123,
                             {"firstname":"Nicolas"}, 
                             callback=callback)
    s2 = DNSServiceAnnouncer("olivo","_test._tcp.",8123,
                             {"firstname":"Paolo"},
                             callback=callback)    
    EventLoop.run()
