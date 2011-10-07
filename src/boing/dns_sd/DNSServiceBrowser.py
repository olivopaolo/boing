# -*- coding: utf-8 -*-
#
# boing/dns_sd/DNSServiceBrowser.py -
#
# Authors: 
#  Nicolas Roussel (nicolas.roussel@inria.fr)
#  Paolo Olivo (paolo.olivo@inria.fr)  
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import logging
import traceback

from boing.dns_sd.dns_sd import *
from boing.dns_sd.DNSService import DNSService
from boing.eventloop.EventLoop import EventLoop

# ---------------------------------------------------------------------------

class DNSServiceBrowser(object):

    def __init__(self, regtype, domain=None, 
                 interface=kDNSServiceInterfaceIndexAny):
        self.logger = logging.getLogger("DNSServiceBrowser.%d"%id(self))
        self.__browsereply = DNSServiceBrowseReply(self.__browsereply)
        self.services = {}
        self.__resolving = {}
        self.__sdRef = DNSServiceRef()
        flags, context = 0, None
        self.__lock = global_lock
        self.__lock.acquire()
        result = dns_sd.DNSServiceBrowse(byref(self.__sdRef),
                                         flags, interface,
                                         regtype.encode(), 
                                         None if domain is None else domain.encode(),
                                         self.__browsereply, 
                                         context)
        self.__lock.release()      
        if result!=kDNSServiceErr_NoError:
            raise RuntimeError("DNSServiceBrowse failed")
        self.__lock.acquire()
        obj = dns_sd.DNSServiceRefSockFD(self.__sdRef)
        self.__lock.release()
        self.__did = EventLoop.if_readable(obj, self.__readable)        
        self.__listeners = []

    def __del__(self):
        EventLoop.cancel_fdhandler(self.__did)
        self.__lock.acquire()
        dns_sd.DNSServiceRefDeallocate(self.__sdRef)
        self.__lock.release()

    def __readable(self, did):
        """If the reference is readable, demand to call the handler."""
        self.__lock.acquire()
        result = dns_sd.DNSServiceProcessResult(self.__sdRef)
        self.__lock.release()
        if result!=kDNSServiceErr_NoError:
            self.logger.warning("DNSServiceProcessResult failed (__readable)")

    def __browsereply(self, sdRef, flags, interface, errorCode,
                      name, regtype, domain, context):
        """Handler method of the browse answer."""
        if errorCode!=kDNSServiceErr_NoError: return  
        service = DNSService(name, regtype, domain, interface)
        key = service.key()
        known_service = key in self.services
        event = None
        if flags&kDNSServiceFlagsAdd:
            if known_service:
                service = self.services[key]
                event = "updated"
            else:
                self.services[key] = service
                event = "found"
        elif known_service:
            del self.services[key]
            event = "lost"
        if event: self.__notify(event, service)
    
    def __notify(self, event, service):
        """Invoke registered listeners to notify browse event."""
        for (callback, args, kwargs) in self.__listeners:
            if isinstance(callback, collections.Callable):
                try:
                    callback(event, service, *args, **kwargs)
                except:
                    traceback.print_exc()

    def addListener(self, callback, *args, **kwargs):
        self.__listeners.append((callback,args,kwargs))
        
# ----------------------------------------------------------------

if __name__=="__main__":
    import sys
    from boing.eventloop.EventLoop import EventLoop
    
    def browserevent(event, service):
        if event=="found":
            print('Service found:')
            print("  " + service.fullname())
            # Add the same handler also to the service in order to get
            # 'txtupdate' and 'resolved' events
            service.addListener(browserevent)
            service.queryTXTrecord()
            service.resolve()
        elif event=="txtupdate":
            print('Event txtupdate:')
            print("  " + service.fullname())
        elif event=="lost":
            print('Service lost:')
        elif event=="resolved":
            print('Service resolved:')
            print("  " + service.fullname())
                               
    try: servicetype = sys.argv[1]
    except: servicetype = "_test._tcp."
    browser = DNSServiceBrowser(servicetype)
    browser.addListener(browserevent)
    print("Listening for %s services:"%servicetype)
    EventLoop.run()
