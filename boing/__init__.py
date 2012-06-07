# -*- coding: utf-8 -*-
#
# boing/__init__.py -
#
# Authors: Paolo Olivo (paolo.olivo@inria.fr)
#          Nicolas Roussel (nicolas.roussel@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

MAJOR = 0
MINOR = 2
VERSION = "%d.%d"%(MAJOR,MINOR)

# -------------------------------------------------------------------
# Facade pattern to make things easier.

from boing.core import Product
from boing.core.economy import Offer, Producer, Consumer, Functor, Identity
from boing.core.querypath import QRequest as Request

from boing.nodes.loader import create
from boing.core.graph import Node

def activateConsole(url="", locals=None, banner=""):
    from boing.utils.url import URL
    from boing.utils import Console    
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

