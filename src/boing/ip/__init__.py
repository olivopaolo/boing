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

from PyQt4.QtNetwork import QAbstractSocket

PF_INET = socket.PF_INET if "PF_INET" in socket.__dict__ else socket.AF_INET
PF_INET6 = socket.PF_INET6 if "PF_INET6" in socket.__dict__ else socket.AF_INET6

"""def IN_MULTICAST(addr):
    return (addr[0]&0xf0==0xe0)

def IN6_IS_ADDR_MULTICAST(addr):
    return (addr[0]==0xff)"""

def resolve(addr, port, family=0, type=0):
    info = socket.getaddrinfo(addr, port, family, type)
    family, socktype, proto, canonname, addr = info[0]
    return addr

def getProtocolFamilyName(family):
    return {PF_INET:"PF_INET", PF_INET6:"PF_INET6"}.get(family,"PF_UNSPEC")

def addrToString(addr):
    """Convert a QHostAddress to string."""
    if addr.protocol()==QAbstractSocket.IPv4Protocol:
        return addr.toString()
    elif addr.protocol()==QAbstractSocket.IPv6Protocol:
        addr = addr.toIPv6Address()
        s = "" ; zeros = False
        for i in range(0,16,2):
            c = (addr[i]<<8)+addr[i+1]
            if c==0:
                if i==0: s += ":"
                if not zeros: 
                    s += ":"
                    zeros = True
            else:
                s += hex(c)[2:]
                if i<14: s += ":"
                if zeros: zeros = False
        return s
    else: return ""


