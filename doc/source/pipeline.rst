===========================
 The pipeline architecture
===========================

|Boing| pipelines are made by directed graphs, where the edge direction
defines the data flow between the nodes. There are three types of
nodes:

- *producers* provide the data;
- *consumers* process the incoming data;
- *workers* are both consumers and producers;

The type of a node directly influences how the node can be connected
to the other nodes: producers only accept outgoing connections, while
consumers accept incoming connections only. Workers are composed by
both the producer and consumer interfaces, so they can have both
incoming and outgoing connections. :ref:`Figure 4.1 <connections>`
shows an example of both valid and invalid connections.

.. _connections:

.. only:: html

   .. figure:: images/connections.svg
      :width: 60 %
      :align: center

      Figure 4.1: Valid and invalid connections between producers (P),
      consumers (C) and workers (W).

.. only:: latex

   .. figure:: images/connections.pdf
      :width: 60 %
      :align: center

      Valid and invalid connections between producers (P), consumers
      (C) and workers (W).

The producer-consumer model
===========================

The core infrastructure of |Boing| pipelines is the producer-consumer
model, which defines how the data is propagated through the
pipeline. The model performs a pull technology, but it is extended by
using the *Observer* pattern: consumers must subscribe to the
producers in order to receive their products; for each subscribed
consumer, producers keep a record containing the list of the pending
products. When a producer has a new product, for each registered
consumer it enqueues the product in the associated product list and it
triggers the consumer, which synchronously or asynchronously can
require its own pending products. Then, at the consumer's request, the
producer sends all the correspondent pending products to the consumer
and it cleans the correspondent buffer. The entire pipeline is run in
a single thread, thus an eventloop is used to handle the asynchronous
nodes. :ref:`Figure 4.2 <postProductSequence>` shows the UML sequence
diagram that defines the data exchange between producers and
consumers.

.. _postProductSequence:

.. only:: html

   .. figure:: images/postProductSequence.svg
      :width: 80 %
      :align: center

      Figure 4.2: UML sequence diagram defining the producer-consumer model

.. only:: latex

   .. figure:: images/postProductSequence.pdf
      :width: 80 %
      :align: center

      UML sequence diagram defining the producer-consumer model

.. seealso::

   classes :class:`boing.core.Producer` and
   :class:`boing.core.Consumer`

Supply and demand
=================

In many situations, a data source can provide a wide range of
information, but consumers may not be interested in all of it. For
this reason, in order to save processing time, the model permits to
assign a request to each consumer. Every time a producer has a new
product, it tests the request of each registered consumer and only if
it matches the product, the producer notifies the consumer the new
product. This behavior enables to process and transfer only the useful
information, while the useless part is not processed. Requests can be
added up so that a producer can easily know the entire request of all
its registered consumers. The union of all the registered consumers'
requests is called *aggregate demand*.

On the other side, it is good to know what a producer can supply. For
this reason the model permits to assign an offer to the producers,
which must be the list of templates of the products it can
provide. Using its offer, a producer can say a priori whether it can
meet a consumer's request. Composing the offer and the aggregate
demand, it is possible to calculate the *demanded offer*, which
represents the subset of the offer that is currently being demanded.

As an example, consider two producers *P1* and *P2* and two consumers
*C1* and *C2* connected as shown in :ref:`figure 4.3
<supplydemand>`. It is possible to observe that the aggregate demand
of *P1* is equal to the union of the requests of both *C1* and
*C2*. Moreover, even if *P1* produces both *A* and *B*, only the
products *A* are sent to *C1*, while both *A* and *B* products are
sent to *C2*. Also note that *P2*'s *demandedOffer* is only *B*,
because *P2* is only connected to *C2* and this one does not require
the products *C*.

.. _supplydemand:

.. only:: html

   .. figure:: images/supplydemand.svg
      :width: 65 %
      :align: center

      Figure 4.3: Example of supply and demand behavior.

.. only:: latex

   .. figure:: images/supplydemand.pdf
      :width: 65 %
      :align: center

      Example of supply and request behavior.

.. note::

   It is important to understand that a node's offer does not impose
   that the only products that the nodes produces are coherent with
   the offer and even that it is sure that the node will ever produce
   such products. The offer is only used to describe the node standard
   behavior. *It's easier said than done!*

.. seealso:: classes :class:`boing.core.Offer` and :class:`boing.core.Request`

As previously seen, it is possible to create long pipelines by
serializing worker nodes. In order to spread the supply and demand
strategy, a worker node must be able to propagate the requests of the
consumers it is connected to in addition to its own request and to
propagate the offer of the producers it is connected to in addition to
its own offer. In order to understand such necessity, consider the
pipeline shown in :ref:`figure 4.4 <propagation>`: in this case the
worker *W* is not propagating its neighbors' requests and offers (the
variables *isPropagantingRequest* and *isPropagatingOffer* are false),
so that its own request and offer, which are defined by the variables
*_selfRequest* and *_selfOffer*, are actually the same of its (public)
request and offer. In this case, it is possible to notice that even if
the consumer *C* require the products *B*, such demand is hidden by
the worker *W*, so that even if the producer *P* can provide *B*
products, it can't see anyone interested to them, so they are not
produced.

.. _propagation:

.. only:: html

   .. figure:: images/propagation.svg
      :width: 90 %
      :align: center

      Figure 4.4: The worker *W* is not propagating its connected
      consumers' requests, thus the producer *P* does not provides the
      products *B*.

.. only:: latex

   .. figure:: images/propagation.pdf
      :width: 90 %
      :align: center

      The worker *W* is not propagating its connected
      consumers' requests, thus the producer *P* does not provides the
      products *B*.

The :ref:`figure 4.5 <propagation2>` shows the same pipeline as before
with the difference that the worker *W* is now propagating its
neighbors' requests and offers. It is possible to notice that the
request of *W* is equal to the union of the request of *C* and its own
request, and its public offer is equal to the union of the offer of
*P* and its own offer. *W* is now requiring *B* products
because a subsequent node is also requiring them, thus *P* will produce
and dispatch them.

.. _propagation2:

.. only:: html

   .. figure:: images/propagation2.svg
      :width: 90 %
      :align: center

      Figure 4.5: Example of supply and demand behavior.

.. only:: latex

   .. figure:: images/propagation2.pdf
      :width: 90 %
      :align: center

      Example of supply and request behavior.

.. note::

   It is important to understand that the variables
   *isPropagatingRequest* and *isPropagatingOffer* do not control the
   output of *W*, but only the fact that its request and offer are
   determined by accumulating the neighbors requests and offers. The
   fact that *W* forwards *B* products only depends on the specific
   implementation of *W*. See class :class:`boing.core.Functor` for
   product forwarding cases.


The wise worker and the auto-configuration feature
==================================================

As formerly described, *worker* nodes are both consumers and
producers, and they can be considered as the pipeline's processing
units. Workers normally calculate simple or atomic operations because
they can be easily serialized in order to compose more complex
processing pipelines. |Boing| pipelines can be modified dynamically in
order to evolve and fit a flexible environment. This may entail that
not all the processing units are really necessary in order to compute
the expected result. In order to avoid a waste of time, the pipeline
exploits a auto-configuration technique based on the nodes'
supply-demand knowledge. This technique, exploited by the *Wise
Workers*, can be summarized into the following two rules:

1. the worker's request is nullified if no one requires the worker's
   own products;

2. the worker's offer is nullified if its own request is not satisfied.

As an example consider the pipeline in :ref:`figure 4.6 <wiseworker>`:
the producer *P* provides the products *A*, which are required by the
consumer *C*; this one also requires the products *B*, but *P* cannot
provide them. For this reason the worker *W*, which can produce *B*
from *A*, has been employed. Since *B* is required by *C*, *W* is
currently active. In this example the worker *W* is set to forward all
the products it receives even it is not directly interested to them.

.. _wiseworker:

.. only:: html

   .. figure:: images/wiseworker.svg
      :width: 90 %
      :align: center

      Figure 4.6: The producer *P* provides the products *A*, while the
      worker *W* produces the products *B* using the products
      *A*. Both *A* and *B* are actually required by the consumer *C*.

.. only:: latex

   .. figure:: images/wiseworker.pdf
      :width: 90 %
      :align: center

      The producer *P* provides the products *A*, while the
      worker *W* produces the products *B* using the products
      *A*. Both *A* and *B* are actually required by the consumer *C*.

Now suppose that the consumer *C* changes its own request to *A*
only. In this case, nobody is interested to *B* anymore, thus,
following the first rule of the *Wise Worker*, the worker stops
requiring *A* for itself and it passes into an inactive state, but,
since it is propagating *C*'s requests, it still requires *A*
products. :ref:`Figure 4.7 <wiseworker2>` shows the state of the
pipeline in this case.

.. _wiseworker2:

.. only:: html

   .. figure:: images/wiseworker2.svg
      :width: 90 %
      :align: center

      Figure 4.7: If *C* does not require products *B* anymore, the
      worker *W* automatically stops producing them and requiring *A*
      products for itself, but since it is propagating *C*'s requests,
      it still requires *A* products so it can forward them to *C*.

.. only:: latex

   .. figure:: images/wiseworker2.pdf
      :width: 90 %
      :align: center

      If *C* does not require products *B* anymore, the worker *W*
      automatically stops producing them and requiring *A* products
      for itself, but since it is propagating *C*'s requests, it still
      requires *A* products so it can forward them to *C*.

Considering the pipeline in :ref:`figure 4.6 <wiseworker>`, a
different situation may arrive: if the producer *P* changes its offer
to *D*, no one will provide the products *A*, thus, following the
second rule of the *Wise Worker*, since the worker's request is not
satisfied anymore, it nullifies its own offer. The resulted pipeline
is shown in :ref:`figure 4.8 <wiseworker3>`. In this case requests do
not change, so that no more products are exchanged between the nodes.

.. _wiseworker3:

.. only:: html

   .. figure:: images/wiseworker3.svg
      :width: 90 %
      :align: center

      Figure 4.8: Considering the pipeline of :ref:`figure 4.6
      <wiseworker>`, if the producer *P* starts producing *B* only,
      the worker's request is not satisfied anymore, so it
      automatically nullifies its default offer.

.. only:: latex

   .. figure:: images/wiseworker3.pdf
      :width: 90 %
      :align: center

      Considering the pipeline of :ref:`figure 4.6 <wiseworker>`, if
      the producer *P* starts producing *D* only, the worker's request
      is not satisfied anymore, so it automatically nullifies its own
      offer.

In some cases workers do not previously know the products they
provide since it only depends on the products they will receive. As
an example, a worker may forward only a subset of the products it
receives or it may make simple changes to the products it requires and
then forward them. In those cases, it is not possible to set the offer
in advance of the pipeline execution, thus the first rule of the *Wise
Worker* cannot be applied. In order to handle those cases, the *Wise
Workers* can use the *Tunneling* exception, that makes the first rule
considering the entire propagated offer instead of the worker's own
offer.

As an example consider the pipeline in :ref:`figure 4.9 <tunneling>`:
the worker *W* simply forwards the products it receives so it has not
its own offer. Despite this, thanks to the tunneling exception, *W* is
still active, since its global offer matches the request of *C*.

.. _tunneling:

.. only:: html

   .. figure:: images/tunneling.svg
      :width: 90 %
      :align: center

      Figure 4.9: When using the tunneling option, the propagated
      offer is considered to determine if the worker is active instead
      of its own offer only.

.. only:: latex

   .. figure:: images/tunneling.pdf
      :width: 90 %
      :align: center

      When using the tunneling option, the propagated
      offer is considered to determine if the worker is active instead
      of its own offer only.

Concrete workers using the tunneling feature are the
:class:`Filter <boing.nodes.Filter>` and
:class:`Calibration <boing.nodes.multitouch.Calibration>` classes.

.. seealso::

   classes :class:`boing.core.WiseWorker` and
   :class:`boing.core.Functor`

.. _node-composition:

.. Node composition
.. ================

.. todo::
   - Describe the composite nodes and node syntax (+ and | operators).

