==============
 Introduction
==============

|boing| enables to create pipelines for connecting different input sources
to multiple target destinations (e.g. applications, logs, etc.)  and
eventually process the data before being dispatched.

As an example, consider the pipeline in :ref:`figure 1.1 <pipeline>`:
two tactile devices (left side) are connected to a single user
application (top-right). At the same time, the contact events from
both the devices are forwarded as a JSON stream to a second remote
application (e.g. a contact visualiser), while an event recorder is
used to log into a file the data stream provided by the second device
only.

.. _pipeline:

.. only:: html

   .. figure:: images/pipeline.svg
      :alt: A pipeline created using |boing|.
      :align: center

      Figure 1.1: Example of pipeline created using |boing|.

.. only:: latex

   .. figure:: images/pipeline.pdf
      :alt: A pipeline created using |boing|.
      :align: center

      Example of pipeline created using |boing|.

Even if the tactile devices provides different data structures
(i.e. TUIO and mtdev), |boing| enables to merge them in a single data
stream (in this example the TUIO and the JSON stream). Contact events
are also processed before being passed to the application: |boing|
provides nodes to smooth or calibrate the input data (e.g. position,
speed, etc.). As shown in the example, pipelines can be composed by
parallel branches so that each input/output can have its own
processing suite.

|boing|  does not impose a specific data model; instead it exploits a
query path language (similar to JSONPath_) for accessing the data to
be processed, so that it can fit a wide range of application domains.

.. _JSONPath: http://goessner.net/articles/JsonPath/
