===================================================
 :mod:`boing.core` --- The pipeline infrastructure
===================================================

.. module:: boing.core
   :synopsis: The pipeline infrastructure

The module :mod:`boing.core` contains all the classes that constitute
the infrastructure of |boing| pipelines.

.. seealso:: :doc:`pipeline`

Producers
=========

.. class:: Producer(offer, tags=None, store=None, retrieve=None, haspending=None, parent=None)

   :class:`Producer` objects are :class:`Observable
   <boing.core.observer.Observable>` objects, which able to post
   products to a set of subscribed :class:`Consumer` instances.

   When a producer is demanded to posts a product, for each registered
   consumer it tests the product with the consumer’s request and only
   if the match is valid it triggers the consumer.

   Each producer can provide an :class:`Offer`, which defines the list
   of products the producer can produce.

   Public signals:

   .. attribute:: demandChanged

      Signal emitted when the aggregate demand changes.

   .. attribute:: offerChanged

      Signal emitted when its own offer changes.

   .. attribute:: demandedOfferChanged

      Signal emitted when its own demanded offer changes.

   Available methods:

   .. method:: aggregateDemand

      Return the union of all the subscribed consumers' requests.

   .. method:: demandedOffer

      Return the producer's demanded offer.

   .. method:: meetsRequest

      Return whether the product's offer meets *request*.

   .. method:: offer

      Return the producer's offer.

   .. method:: postProduct(product)

      Post *product*. In concrete terms, it triggers the registered
      consumers that require *product*, then it stores the product.

.. class:: Offer(*args, iter=None)

   An :class:`Offer` defines the list of products that a producer
   advertises to be its deliverable objects.

   .. note:: A producer's offer only estimates the products that
      are normally produced. There is no guarantee that such products
      will ever be posted, neither that products that do not match the
      offer won't be produced.

   :const:`Offer.UNDEFINED` can be used to define the producer's
   offer, when the real offer cannot be defined a priori. This avoids
   to have empty offers, when they cannot be predeterminated.

Consumers
=========

.. class:: Consumer(request, consume=None, hz=None, parent=None)

   :class:`Consumer` objects are :class:`Observer
   <boing.core.observer.Observer>` objects that can be subscribed to
   several :class:`Producer` instances for receiving their
   products. When a producer posts a product, it triggers the
   registered consumers; then the consumers will immediately or at
   regular time interval demand to the producer the new products.

   .. warning:: Many consumers can be subscribed to a single
      producer. Each new product is actually shared within the
      different consumers, therefore a consumer **MUST NOT** modify
      any received product, unless it is supposed to be the only
      consumer.

   Consumers have a :class:`Request`. When a producer is demanded to
   posts a product, it tests the product with the consumer's request
   and only if the match is valid it triggers the consumer.

   .. method:: request

      Return the consumer’s request.

   .. method:: _consume(products, producer)

      Consume the *products* posted from *producer*.

.. class:: Request

   The class :class:`Request` is an abstract
   class used by :class:`Consumer` objects for
   specifing the set of products they are insterested to. The method
   :meth:`test` is used to check whether a product matches the
   request.

   :const:`Request.NONE` and :const:`Request.ANY` define respectively
   a "no product" and "any product" requests.

   :class:`Request` objects may also indicate the
   internal parts of a product to which a producer may be
   interested. The method :meth:`items` returns the sequence of the
   product's parts a producer is interested to.

   The class :class:`Request` implements the
   design pattern "Composite": different requests can be combined into
   a single request by using the sum operation (e.g. :code:`comp =
   r1 + r2`). A composite request matches the union of the products
   that are matched by the requests whom it is
   composed. :const:`Request.NONE` is the identity element of the sum
   operation.

   :class:`Request` objects are immutable.

   .. method:: test(product)

      Return whether the *product* matches the request.

   .. method:: items(product)

      Return an iterator over the *product*'s internal parts
      (i.e. (key, value) pairs) that match the request.

.. class:: QRequest(string)

   The :class:`QRequest` is a :class:`Request` defined by a :class:`QPath
   <boing.utils.qpath.QPath>`.
