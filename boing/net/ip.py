# -*- coding: utf-8 -*-
#
# boing/net/ip.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

"""The module :mod:`boing.net.ip` provides few functions related to
IP addressing.

"""

import socket

from PyQt4.QtNetwork import QAbstractSocket, QHostAddress
from boing.utils import assertIsInstance

PF_INET = socket.PF_INET if "PF_INET" in socket.__dict__ else socket.AF_INET
PF_INET6 = socket.PF_INET6 if "PF_INET6" in socket.__dict__ else socket.AF_INET6

"""def IN_MULTICAST(addr):
    return (addr[0]&0xf0==0xe0)

def IN6_IS_ADDR_MULTICAST(addr):
    return (addr[0]==0xff)"""

def resolve(addr, port, family=0, type=0):
    """Return a pair (addr, port) representing the IP address
    associated to the host *host* for the specified port, family and
    socket type."""
    info = socket.getaddrinfo(addr, port, family, type)
    family, socktype, proto, canonname, addr = info[0]
    return addr

def addrToString(addr):
    """Return a string representing the QHostAddress *addr*."""
    assertIsInstance(addr, QHostAddress)
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

def getProtocolFamilyName(family):
    return {PF_INET:"PF_INET", PF_INET6:"PF_INET6"}.get(family,"PF_UNSPEC")


