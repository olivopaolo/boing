# -*- coding: utf-8 -*-
#
# boing/ip/__init__.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import socket

PF_INET = socket.PF_INET if "PF_INET" in socket.__dict__ else socket.AF_INET
PF_INET6 = socket.PF_INET6 if "PF_INET6" in socket.__dict__ else socket.AF_INET6

def IN_MULTICAST(addr):
    return (addr[0]&0xf0==0xe0)

def IN6_IS_ADDR_MULTICAST(addr):
    return (addr[0]==0xff)

def resolve(addr, family, type):
    if addr is None: return None
    info = socket.getaddrinfo(addr[0] if addr[0] else None, 
                              addr[1], 
                              family, type)
    family, socktype, proto, canonname, addr = info[0]
    return addr

def getProtocolFamilyName(family):
    return {PF_INET:"PF_INET", PF_INET6:"PF_INET6"}.get(family,"PF_UNSPEC")
