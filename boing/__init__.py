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

# Facade pattern to make things easier.
from boing import core

class Offer(core.economy.Offer):
    """An offer defines the list of products that a producer
    advertises to be its deliverable objects.

    """
    pass

class Request(core.economy.Request):
    """The Request abstract class defines objects for filtering
    products.  Each consumer has got a request so that producers know
    if it is useful or not to deliver a product to a consumer.

    Request.NONE and Request.ANY define respectively 'no product' and
    'any product' requests.

    The Request class implements the Composite design
    pattern. Composite requests can be obtained simply adding singular
    requests, e.g. comp = r1 + r2. Request.NONE is the identity
    element of Request sum.

    Request instances are immutable objects.

    """
    pass

class LambdaRequest(core.economy.LambdaRequest):
    """The LambdaRequest is a Request that can be initialized using a
    lambda function.

    """
    pass

class QRequest(core.querypath.QRequest):
    """The QRequest is a Request defined by a QPath.

    """
    pass

class Producer(core.economy.Producer):
    """A Producer is an observable object enabled to post products to
    a set of subscribed consumers.

    When a producer is demanded to posts a product, for each
    registered consumer it tests the product with the consumer's
    request and only if the match is valid it triggers the consumer.

    Each Producer has an Offer (a list of product templates), so it
    can say if a priori it can meet a consumer's request.

    """
    pass

class Consumer(core.economy.Consumer):
    """A Consumer is an observer object that can be subscribed to many
    producers for receiving their products. When a producer posts a
    product, it triggers the registered consumers; the triggered
    consumers will immediately or at regular time interval demand the
    producer the new products.

    Many consumers can be subscribed to a single producer. Each new
    product is actually shared within the different consumers,
    therefore a consumer SHOULD NOT modify any received product,
    unless it is supposed to be the only consumer.

    Consumers have a request. When a producer is demanded to posts a
    product, it tests the product with the consumer's request and only
    if the match is valid it triggers the consumer.

    A consumer's request must be an instance of the class Request. The
    requests 'Request.NONE' and "Request.ANY" are available for
    selecting none or any product.

    """
    pass

class Functor(core.economy.Functor):
    pass

class Identity(core.economy.Identity):
    pass

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
