# -*- coding: utf-8 -*-
#
# boing/net/ntp.py -
#
# Author: Nicolas Roussel (nicolas.roussel@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

"""The module :mod:`boing.net.ntp` provides few functions for handling
the `Network Time Protocol (NTP) <http://www.ntp.org/>`_.

*Example*::

    import datetime
    from boing.net import ntp
    srvtime = ntp.ntpFromServer("europe.pool.ntp.org")
    srvdatetime = ntp.ntp2datetime(srvtime)
    now = datetime.datetime.now()
    print("Server time:", srvdatetime)
    print("Local time:", now)
    print("Delta:", now - srvdatetime)

"""


import datetime
import struct
import time

# See
#   http://tools.ietf.org/html/rfc958
#   http://en.wikipedia.org/wiki/Network_Time_Protocol
#   http://en.wikipedia.org/wiki/Unix_time
#   http://seehuhn.de/pages/pdate

_kUnixEpoch = 2208988800  # 1970-01-01T00:00:00Z
_kNtpFrac   = 4294967296.0 # 2^32

def _dump(data):
    import io
    output = io.StringIO()
    output.write("[")
    format = lambda c: "%x"%ord(c)
    output.write(" ".join(map(format,data)))
    output.write("]")
    return output.getvalue()

def ntpDecode(data):
    """Return the POSIX timestamp obtained from decoding the bytes object
    *data*."""
    #print "ntpDecode:",_dump(data)
    seconds, picoseconds = struct.unpack("!2I", data)
    #print "ntpDecode:", seconds, picoseconds
    return seconds + picoseconds/_kNtpFrac

def ntpEncode(t):
    """Return the bytes object obtained from encoding the POSIX
    timestamp *t*."""
    seconds = int(t)
    picoseconds = int((t-seconds)*_kNtpFrac)
    #print "ntpEncode:", seconds, picoseconds
    data = struct.pack("!2I", seconds, picoseconds)
    #print "ntpEncode:",_dump(data)
    return data

def ntpFromServer(server):
    """Send an ntp time query to the *server* and return the obtained
    POSIX timestamp. The request is sent by using an UDP connection to
    the port 123 of the NTP server."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = '\x1b' + 47 * '\0'
    sock.sendto(data.encode(), (server, 123))
    data, address = sock.recvfrom(1024)
    return ntpDecode(data[40:48])

def ntp2datetime(t):
    """Return the :class:`datetime.datetime` instance corresponding to
    the POSIX timestamp *t*."""
    return datetime.datetime.fromtimestamp(t-_kUnixEpoch)

def datetime2ntp(dt):
    """Return the POSIX timestamp corresponding to the
    :class:`datetime.datetime` instance *dt*."""
    return _kUnixEpoch + time.mktime(dt.timetuple())+1e-6*dt.microsecond

# -------------------------------------------------------------------------

if __name__=="__main__":
    import sys
    try:
        server = sys.argv[1]
    except:
        server = "127.0.0.1"
    print("Sending query to",server)
    t1 = ntpFromServer(server)
    print("t1:",t1)
    dt = ntp2datetime(t1)
    print("dt:",dt)
    t2 = datetime2ntp(dt)
    print("t2:",t2,t1-t2)
    data = ntpEncode(t1)
    #print(_dump(data))
    t3 = ntpDecode(data)
    print("t3:",t3,t1-t3)
    data = ntpEncode(t2)
    t4 = ntpDecode(data)
    print("t4:",t4,t1-t4)
