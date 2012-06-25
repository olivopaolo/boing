
boing
=====

.. automodule:: boing

.. autofunction:: boing.create

This module provides the following class:

.. autoclass:: boing.Offer
   :members: UndefinedProduct

.. autoclass:: boing.Request
   :members: ANY, NONE, test, items, filter, filterout,

.. autoclass:: boing.QRequest

.. autoclass:: boing.Producer
   :members: demandChanged, offerChanged, demandedOfferChanged, aggregateDemand, demandedOffer, meetsRequest, offer, postProduct

.. autoclass:: boing.Consumer
   :members: request, _consume


Submodules:

.. toctree::
   boing.core
   boing.gesture
   boing.net
   boing.nodes
   boing.utils
