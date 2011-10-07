# -*- coding: utf-8 -*-
#
# boing/dns_sd/dns_sd.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import sys
from ctypes import *
from ctypes.util import find_library

# ---------------------------------------------------------------------------
#
# From /usr/include/dns_sd.h
#
# http://developer.apple.com/documentation/networking/Reference/DNSServiceDiscovery_CRef/dns_sd/


class _DummyLock(object):

    @staticmethod
    def acquire():
        pass

    @staticmethod
    def release():
        pass

global_lock = _DummyLock()

if sys.platform == 'win32':
    _cfunc = WINFUNCTYPE
    dns_sd = windll.dnssd
elif sys.platform=="darwin":
    _cfunc = CFUNCTYPE
    dns_sd = cdll.LoadLibrary(find_library("System"))
elif sys.platform=="linux2":
    # If libdns_sd is actually Avahi's Bonjour compatibility
    # layer, silence its annoying warning messages, and use a real
    # RLock as the global lock, since the compatibility layer
    # isn't thread safe.
    _cfunc = CFUNCTYPE
    dns_sd = cdll.LoadLibrary(find_library("dns_sd"))
    import os, threading
    os.environ['AVAHI_COMPAT_NOWARN'] = '1'
    global_lock = threading.RLock()
else:
    raise Exception("Unsupported platform, %s", sys.platform)

DNSServiceFlags = c_uint32
DNSServiceErrorType = c_int32

DNSServiceRef = c_void_p

DNSServiceRegisterReply = _cfunc(None,                # return type
                                 DNSServiceRef,       # sdRef
                                 DNSServiceFlags,     # flags
                                 DNSServiceErrorType, # errorCode
                                 c_char_p,            # name
                                 c_char_p,            # regtype
                                 c_char_p,            # domain,
                                 c_void_p)            # context

DNSServiceBrowseReply = _cfunc(None, # return type
                               DNSServiceRef,       # sdRef
                               DNSServiceFlags,     # flags
                               c_uint32,            # interfaceIndex
                               DNSServiceErrorType, # errorCode
                               c_char_p,            # serviceName
                               c_char_p,            # regtype
                               c_char_p,            # replyDomain
                               c_void_p)            # context

DNSServiceResolveReply = _cfunc(None, # return type
                                DNSServiceRef,       # sdRef
                                DNSServiceFlags,     # flags
                                c_uint32,            # interfaceIndex
                                DNSServiceErrorType, # errorCode
                                c_char_p,            # fullname
                                c_char_p,            # hosttarget
                                c_uint16,            # port
                                c_uint16,            # txtLen
                                c_void_p,            # txtRecord, not null terminated
                                c_void_p)            # context

DNSServiceQueryRecordReply = _cfunc(None, # return type
                                    DNSServiceRef,       # sdRef
                                    DNSServiceFlags,     # flags
                                    c_uint32,            # interfaceIndex
                                    DNSServiceErrorType, # errorCode
                                    c_char_p,            # fullname
                                    c_uint16,            # rrtype
                                    c_uint16,            # rrclass
                                    c_uint16,            # rdlen
                                    c_void_p,            # rdata
                                    c_uint32,            # ttl
                                    c_void_p)            # context

# Constants for specifying an interface index
kDNSServiceInterfaceIndexAny       = 0
kDNSServiceInterfaceIndexLocalOnly = 4294967295 # ((uint32_t)-1)
kDNSServiceInterfaceIndexUnicast   = 4294967294 # ((uint32_t)-2)

# Possible error code values
kDNSServiceErr_NoError = 0
kDNSServiceErr_NameConflict = -65548

# General flags
kDNSServiceFlagsAdd = 0x2

# Maximum lengths
kDNSServiceMaxServiceName = 64
kDNSServiceMaxDomainName  = 1005

# DNS Classes and Types (listed in RFC 1035)
kDNSServiceClass_IN =  1
kDNSServiceType_TXT = 16
kDNSServiceType_SRV = 33

# ---------------------------------------------------------------------------

try:
    if sys.platform=='win32':
        __lib = windll.iphlpapi
    else:
        __lib = cdll.LoadLibrary(find_library("c"))
    def if_indextoname(index):
        name = {kDNSServiceInterfaceIndexAny:"Any",
         kDNSServiceInterfaceIndexLocalOnly:"LocalOnly",
         kDNSServiceInterfaceIndexUnicast:"Unicast"}.get(index, None)
        if name is not None: return name
        tmp = create_string_buffer(16*4)
        if __lib.if_indextoname(index, tmp)==0: return "Unknown"
        return tmp.value
    if_nametoindex = __lib.if_nametoindex
except:
    if_indextoname = lambda x: "Unknown"
    if_nametoindex = lambda x: 0
