===================================================
 :mod:`boing.core` --- The pipeline infrastructure
===================================================

.. automodule:: boing.core

.. autoclass:: boing.core.Offer

.. autoclass:: boing.core.Request
   :members: test, items

.. autoclass:: boing.core.QRequest

.. autoclass:: boing.core.Producer
   :members: demandChanged, offerChanged, demandedOfferChanged, aggregateDemand, demandedOffer, meetsRequest, offer, postProduct

.. autoclass:: boing.core.Consumer
   :members: request, _consume
