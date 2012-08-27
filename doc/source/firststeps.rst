=============
 First steps
=============

This tutorial helps you starting to use the |boing| toolkit by
providing simple examples of the toolkit's fuctionalities.

Let's consider to have a multi-touch input device, like a tablet or a
touch-screen. What cool things can I do with |boing|? |boing| enables to
create a pipeline for connecting your device to different targets,
like applications, frameworks, debuggers and eventually processing the
gesture events before having being dispatched, like for example
calibrate the contacts' position or apply a smoothing filter.

To make things easier, let's consider that your device can send the
information of the contact events as a TUIO stream on the local
port 3333. [#]_


Showing multi-touch events
==========================

First of all, it is important to know that all the |boing|'s tools are
invoked by using the script :command:`boing`. Open a terminal and
type::

   boing "in.tuio: + viz:"

The script should have opened a window displaying a grid. Now when you
touch your multi-touch device, you will be able to see the contact
points appear on the window.

It's not difficult to notice that the script accepts a single argument
that defines the configuration of the pipeline that is to be
created. Configurations are defined by a formula where the operands
define the functionality of the nodes of the pipeline, while the
operators define how the nodes are connected, therefore also the
structure of the pipeline. [#]_

In the previous example, the pipeline was composed by two nodes:

- :code:`in.tuio:` corresponds to a node that reads the socket,
  decodes the TUIO stream and provides the multi-touch events;
- :code:`viz:` corresponds to the *Contact Visualizer*, a widget
  that shows the information of the contact points, such as position,
  track and speed.

The two nodes are joined using the :code:`+` operator, which stands
for connection *in series*. The structure of the pipeline is
represented in :ref:`figure 3.1 <figure1>`.

.. _figure1:
.. only:: html

   .. figure:: images/firststeps1.svg
      :align: center

      Figure 3.1: Pipeline obtained from the configuration
      :code:`in.tuio: + viz:`.

.. only:: latex

   .. figure:: images/firststeps1.pdf
      :align: center

      Pipeline obtained from the configuration
      :code:`in.tuio: + viz:`.

Congratulations! You have created your first |boing| pipeline!

Exploring the data
==================

Now, let's try new functionalities by adding new nodes. Stop the
previous pipeline by closing the visualizer widget or pressing Ctrl-C
on the terminal, and type in the terminal::

  boing "in.tuio: + (viz: | dump:)"

As before the contact visualizer appears again, but this time, when
you touch the multi-touch device, the terminal prints a lot of data!
The terminal output represents all the data that the :code:`in.tuio:`
node can produce and send to the connected nodes. This tutorial is not
aimed to provide an exaustive description of the message structure;
for the moment, simply observe that data messages are hierarchical
structures mainly composed by Python built-in types, such as
dictionaries, lists, strings, bytearrays, etc. Thanks to such standard
structure, |boing| exploits a query language, similar to JSONPath_,
for the indexing or the filtering of data messages. In order to
understand the usefulness of such query language, stop the pipeline
and type in the terminal::

  boing "in.tuio: + (viz: | dump:?request=$..contacts)"

Now, when you touch your multi-touch device, you can see that the
terminal prints the subset of the data structures that refers only to
the contact data. This is because the query :code:`$..contacts`
addresses to any data named as :code:`contact`, searched at any level
of the structure. Such query language can be very useful during
development and testing phases for highlighting only the relevant
information.

A more exhaustive description of the data structure and the query
language can be found in the :doc:`../functionalities` section. For
now, let's leave the data structure and we consider the functioning of
the pipeline: it's not difficult to understand that the :code:`|`
operator (*Pipe*) is used to connect in parallel the nodes :code:`viz:` and
:code:`dump:`, so that the products are sent to both of
them. :ref:`Figure 3.2 <figure2>` shows the structure of the current
pipeline.

.. _figure2:
.. only:: html

   .. figure:: images/firststeps2.svg
      :align: center

      Figure 3.2: Pipeline obtained from the configuration
      :code:`in.tuio: + (viz: | dump:)`.

.. only:: latex

   .. figure:: images/firststeps2.pdf
      :align: center

      Pipeline obtained from the configuration :code:`in.tuio: +
      (viz: | dump:)`.

Combining input sources with external applications
==================================================


A key feature of |boing| is the ability to provide the captured input
events to external applications. This enables in most of the cases to
take advantage of the toolkit's features without the need to adapt or
to modify the applications, while sometimes a simple configuration may
be required. As shown in :ref:`figure 3.3 <figure3>`, the Boing
toolkit works as a semi-transparent layer placed between the input
sources and the final applications.

.. _figure3:
.. only:: html

   .. figure:: images/firststeps3.svg
      :align: center

      Figure 3.3: Boing works as a semi-transparent layer placed in
      between the devices and the applications for processing and
      transmitting the input events.

.. only:: latex

   .. figure:: images/firststeps3.pdf
      :align: center

      Boing works as a semi-transparent layer placed in between the
      devices and the applications for processing and transmitting the
      input events.

Thanks to the many supported encodings, |boing| can easily fit different
combinations of devices and applications. In this basic example, let's
consider to have an application listening for a TUIO stream on the
local port 3335 [#]_. If you don't have a TUIO application, simply open a
new terminal and launch a new |boing| instance using the command::

   boing "in.tuio://:3335 + viz:"

In the previous example you connected one input device to two output
nodes. The :code:`|` operator also enables to put in parallel
different inputs, like for example a second multi-touch device enabled
to send its TUIO messages to the local port 3334. Let's try a new
pipeline by running the command::

   boing "(in.tuio: | in.tuio://:3334) + (viz: | out.tuio://[::1]:3335)"

Note that for the first input it has not been necessary to define the
port number, since the default port for the TUIO protocol is
the 3333. For the second one instead the port number has been defined
to 3334. :ref:`Figure 3.4 <figure4>` shows the structure of the new
pipeline.

.. _figure4:
.. only:: html

   .. figure:: images/firststeps4.svg
      :align: center

      Figure 3.4: Pipeline obtained from the configuration

      :code:`(in.tuio: | in.tuio://:3334) + (viz: | out.tuio://[::1]:3335)`.

.. only:: latex

   .. figure:: images/firststeps4.pdf
      :align: center

      Pipeline obtained from the configuration :code:`(in.tuio: |
      in.tuio://:3334) + (viz: | out.tuio://[::1]:3335)`.

As you can see, a very important feature of |boing| is that you can
simultaneously connect many devices to different applications. Such
feature eases the usage of debugging tools and enables multi-device
and multi-user applications.

Input data processing
=====================

.. todo:: Describe the filtering, calibration functionalities.


Event recording and replaying
=============================

.. todo:: Describe the filtering, calibration functionalities.

.. rubric:: Footnotes

.. [#] If you are unfamiliar with the TUIO protocol, consider having a look to the available `TUIO trackers`_, or jumping to the :doc:`multitouch`, in order to discover the different ways |boing| exploits to connect to the input devices.

.. [#] For a deeper presentation of pipeline configurations, see the :doc:`../functionalities` section.

.. [#] For more output sources, see the :doc:`../functionalities` section.

.. _`TUIO trackers`: http://www.tuio.org/?software
.. _JSONPath: http://goessner.net/articles/JsonPath/
