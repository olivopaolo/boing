========================================
 :mod:`boing.net.ntp` --- NTP utilities
========================================

.. module:: boing.net.ntp
   :synopsis: NTP utilities

The module :mod:`boing.net.ntp` provides few functions for handling
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


..  function:: ntpEncode(t)

    Return the bytes object obtained from encoding the POSIX timestamp
    *t*.

..  function:: ntpDecode(data)

    Return the POSIX timestamp obtained from decoding the bytes object
    *data*.

..  function:: ntpFromServer(server)

    Send an ntp time query to the *server* and return the obtained
    POSIX timestamp. The request is sent by using an UDP connection to
    the port 123 of the NTP server.

..  function:: ntp2datetime(t)

    Return the :class:`datetime.datetime` instance corresponding to
    the POSIX timestamp *t*.

..  function:: datetime2ntp(dt)

    Return the POSIX timestamp corresponding to the
    :class:`datetime.datetime` instance *dt*.
