# -*- coding: utf-8 -*-
#
# boing/__init__.py -
#
# Authors: Paolo Olivo (paolo.olivo@inria.fr)
#          Nicolas Roussel (nicolas.roussel@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

MAJOR = 0
MINOR = 2
VERSION = "%d.%d"%(MAJOR,MINOR)

from boing.nodes.loader import create
from boing.core.graph import Node

def activateConsole(url="", locals=None, banner=None):
    """Enable a Python interpreter at *url*.

    The optional *locals* argument specifies the dictionary in which
    code will be executed; it defaults to a newly created dictionary
    with key "__name__" set to "__console__" and key "__doc__" set to
    None.

    The optional *banner* argument specifies the banner to print
    before the first interaction; by default it prints a banner
    similar to the one printed by the real Python interpreter.

    """
    from boing.utils.url import URL
    from boing.utils import Console
    if locals is None: locals = dict(__name__="__console__",
                                     __doc__=None)
    if banner is None:
        import sys
        banner="Boing 0.2 Console\nPython %s on %s\n"%(sys.version,
                                                       sys.platform)
    if not url:
        import sys
        from boing.utils.fileutils import CommunicationDevice, IODevice
        console = Console(CommunicationDevice(sys.stdin), IODevice(sys.stdout),
                          locals=locals, banner=banner)
    else:
        from boing.net import tcp
        from boing.utils.url import URL
        if not isinstance(url, URL): url = URL(url)
        def newConnection():
            socket = console.nextPendingConnection()
            c = Console(socket, socket, locals=locals, parent=console)
        console = tcp.TcpServer(url.site.host, url.site.port,
                                newConnection=newConnection)
    return console
