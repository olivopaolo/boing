======================================
 :mod:`boing.net.ip` --- IP utilities
======================================

.. module:: boing.net.ip
   :synopsis: IP utilities

The module :mod:`boing.net.ip` provides few functions related to
IP addressing.

.. function:: resolve(addr, port, family=0, type=0)

   Return a pair (addr, port) representing the IP address associated
   to the host *host* for the specified port, family and socket type.

.. function:: addrToString(addr)

   Return a string representing the QHostAddress *addr*.
