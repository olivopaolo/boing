===================================================
 :mod:`boing.core` --- The pipeline infrastructure
===================================================

.. module:: boing.core
   :synopsis: The pipeline infrastructure

The module :mod:`boing.core` contains all the classes that constitute
the infrastructure of |boing| pipelines.

The :class:`Producer` and :class:`Consumer` classes are build over the
Observer design pattern of the module :mod:`boing.core.observer`: the
Producer is an Observable object enabled to post products; a consumer
is an Observer object that can subscribe itself to many
producers. When a producer has a new product, it triggers the
registered consumers; the triggered consumers will immediately or at
regular time interval demand the producer the new products.

A :class:`Worker` object is both a :class:`Producer` and a
:class:`Consumer` and it is used as base class for defining processing
nodes. By connecting producers, workers and consumers it is possible
to create processing pipelines.

A :class:`WiseWorker` is a :class:`Worker` able to automatically
detect whenever it should not propose its own offer or its own
request; this is done in order to save computational time.

The :class:`Functor` class is practical base class for inheriting
custom processing :class:`Worker` objects. Instead of implementing the
classic :meth:`Consumer._consume` method, the :class:`Functor`
proposes the more powerfull method :meth:`Functor._process`.

Multiple :class:`Producer`, :class:`Consumer` and :class:`Worker`
instances can be composed into :class:`Composite` objects. There are
three types of composites:

- a :class:`CompositeProducer` works as it was a single producer;
- a :class:`CompositeConsumer` works as it was a single consumer;
- a :class:`CompositeWorker` works as it was a single worker;

.. seealso:: :doc:`pipeline`


Producers
=========

.. class:: Producer(offer, tags=None, store=None, retrieve=None, haspending=None, parent=None)

   :class:`Producer` instances are :class:`Observable
   <boing.core.observer.Observable>` objects able to post products to
   a set of subscribed :class:`Consumer` instances. The argument
   *offer* must be an instance of :class:`Offer` and it define the
   products this producer will supply, while *tags* must be a dict or
   None. The argument *store* can be a callable object to be used as a
   handler for storing posted products (see :meth:`_store` for the
   handler arguments) or None, while *retrieve* can be a callable
   object to be used as a handler for retrieving stored products (see
   :meth:`_retrieveAndDeliver` for the handler arguments) or
   None. *parent* defines the consumer's parent.

   When a producer is demanded to posts a product, for each registered
   consumer it tests the product with the consumer’s request and only
   if the match is valid it triggers the consumer.

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

   The class :class:`Request` is an abstract class used by
   :class:`Consumer` objects for specifing the set of products they
   are insterested to. The method :meth:`test` is used to check
   whether a product matches the request.

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

Workers
=======

.. class:: Worker

   A :class:`Worker` instance is both a :class:`Producer` and a
   :class:`Consumer`. The class :class:`Worker` is by itself an
   abstract class. Consider using the concrete class
   :class:`BaseWorker` instead.


.. class:: BaseWorker(request, offer, tags=None, store=None, retrieve=None, haspending=None, consume=None, hz=None, parent=None)

   A :class:`BaseWorker` is the simplest concrete :class:`Worker`. By
   default it does nothing with the products it receives, but it is
   able to propagate the offers of the producers it is subscribed to,
   and it is able to propagate the requests of the consumers that are
   subscribed to it.


.. class:: NopWorker(store=None, retrieve=None, hz=None, parent=None)

   :class:`NopWorker` instances simply forwards all the products they
   receive.


.. class:: WiseWorker(request, offer, **kwargs)

   A :class:`WiseWorker` instance is able to automatically detect
   whenever it should not propose its own offer or its own request;
   this is done in order to save computational time.  The behaviour of
   :class:`WiseWorker` objects works as follows:

   1. Its own request is deactivated if there is no consumer
      insterested to its offer (i.e. no items in demandedoffer), which
      means: <<If nobody is interested to its products, why should it
      requires the products necessary to the processing?>>.

   2. Its own offer is deactivated if there is no producer that meets
      its request, which means: <<If nobody can provide it the
      products it requires for processing, how can it propose its
      offer?>>.

   A :class:`WiseWorker` is active (see method :meth:`isActive`) when
   its own request is not deactivated (i.e. case 1).

   A :class:`WiseWorker` can be forced to be activated or
   deactivated. Use the method :meth:`setForcing` to impose a specific
   behaviour.

   Use :const:`WiseWorker.TUNNELING` as the worker Offer, when the
   worker is supposed to process and then forward a subset of the
   products it receives. This is necessary since sometimes it may be
   possible that the worker cannot have a predefined offer since it
   always depend from the offer of the observed producers.

   .. method:: isActive()

      The :class:`WiseWorker` is active only if its offer is requested
      from any subscribed consumer, unless it is forced (see
      :meth:`forcing`).

   .. method:: isTunneling()

      Return True if the worker is forwarding a subset of the products
      it receives.

   .. method:: forcing()

      Return whether the WiseWorker is being forced. Return a value
      within (:const:`WiseWorker.ACTIVATED`,
      :const:`WiseWorker.DEACTIVATED`, :const:`WiseWorker.NONE`).

   .. method:: setForcing(forcing)

      Impose to the :class:`WiseWorker` to be activated, deactivated
      or remove a previous forcing. *forcing* must be a value within
      (:const:`WiseWorker.ACTIVATED`, :const:`WiseWorker.DEACTIVATED`,
      :const:`WiseWorker.NONE`).

   .. attribute:: ACTIVATED

      Value used to force the :class:`WiseWorker` to be activated.

   .. attribute:: DEACTIVATED

      Value used to force the :class:`WiseWorker` to be deactivated.

   .. attribute:: NONE

      Value used to let the :class:`WiseWorker` decide it it should be
      active.

   .. attribute:: TUNNELING

      Value used to set the :class:`WiseWorker` the tunneling mode.

.. class:: Functor(args, offer, blender, process=None, **kwargs)

   The :class:`Functor` class is practical base class for inheriting
   custom processing :class:`Workers`. Instead of implementing the
   classic :meth:`Consumer._consume` method, the :class:`Functor`
   proposes the more powerfull method :meth:`_process`. This handler
   method receives as argument *sequence*, an iterator over the
   operands, which are iterators over the couples (key, value)
   obtained from applying the method :meth:`Request.items` of the
   request of the functor on the list of received products. This
   enables to access directly to the name and values of the required
   data without the need of reimplementing the code to get them. The
   method :meth:`_process` is a generator method and it it supposed to
   yield the the couples (key, value) representing the result of the
   node processing. The yielded results are automatically considered
   by the functor to create a new product that will be automatically
   posted.

   The functor uses a :class:`Functor.Blender` object to create the
   new product. A set of predefined blenders are used to set the
   functor behaviour:

   - :const:`Functor.MERGE` --- Join the original product and results
     of the functor.

   - :const:`Functor.MERGECOPY` --- Make a deep copy of the original
     product and then join the results of the functor.

   - :const:`Functor.RESULTONLY` --- Post as product only the result of
     the functor.

   A :class:`Functor` instance propagates the requests only if the
   current blender is a :class:`MergeBlender` and it propagates the
   offers only if the current blender is a :class:`MergeBlender` or if
   it is tunneling (see :meth:`WiseWorker.isTunneling`).

   .. method:: blender()

      Return the current active :class:`Functor.Blender`.

   .. method:: _process(sequence, producer)

      This handler method receives as argument *sequence*, an iterator
      over the operands, which are iterators over the couples (key,
      value) obtained from applying the method :meth:`Request.items`
      of the request of the functor on the list of received
      products. This enables to access directly to the name and values
      of the required data without the need of reimplementing the code
      to get them. This is a generator method and it it supposed to
      yield the the couples (key, value) representing the result of
      the node processing.


Composites
==========

.. class:: Composite(*internals, parent=None)

   A :class:`Composite` instance stores a set of internal objects
   using strong references. Use the method :meth:`internals` to scroll
   the references objects.

   .. method:: internals()

      Return an iterator over the set of internal nodes for which a
      strong reference is stored.

.. class:: CompositeProducer(*producers, internals=set(), parent=None)

   A :class:`CompositeProducer` combines in parallel the list of
   *producers* so that they can be considered as a single
   :class:`Producer`. The argument *internals* can be used to specify
   the object for which a strong reference should be kept. All
   *producers* are by default added as internals of the
   :class:`Composite`.

   .. method:: producers()

      Return an iterator over the first level producers.

.. class:: CompositeConsumer(*consumers, internals=set(), parent=None)

   A :class:`CompositeConsumer` combines in parallel the list of
   *consumers* so that they can be considered as a single
   :class:`Consumer`. The argument *internals* can be used to specify
   the object for which a strong reference should be kept. All
   *consumers* are by default added as internals of the
   :class:`Composite`.

   .. method:: consumers()

      Return an iterator over the first level consumers.


.. class:: CompositeWorker(consumers, producers, internals=set(), parent=None)

   A :class:`CompositeWorker` object combines in parallel the list of
   *producers* and in parallel the list of *consumers* so that they
   can be considered as a single :class:`Worker`. The argument
   *internals* can be used to specify the object for which a strong
   reference should be kept. All *producers* and *consumers* are by
   default added as internals of the :class:`Composite`.
