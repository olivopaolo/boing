=========================================
 boing - Creating and managing pipelines
=========================================

Developers can easily deploy Boing pipelines by invoking the toolkit's
API in their Python code. The most important element is the function
:func:`boing.create`, which is used to instantiate the nodes of
the pipeline.

.. autofunction:: boing.create

All the available nodes are listed and described in the :doc:`uris`.

In order to compose the pipeline, the nodes can be attached using the
Python operators :code:`+` and :code:`|`, which work the same as the
operators used in the URI expressions. As an example, consider the
following code::

   n1 = boing.create("in.tuio:")
   n2 = boing.create("viz:")
   n3 = boing.create("dump:")
   pipeline = n1 + (n2 | n3)

The same pipeline can be obtained using the following code::

   pipeline = boing.create("in.tuio:+(viz:|dump:)")

In order to run the pipeline it is necessary to launch the Qt
Application that should have been initialized before creating the
pipeline. The following code can be used as an example for creating
custom |boing| pipelines::

   #!/usr/bin/env python3
   import sys
   import PyQt4
   import boing

   # Init application
   app = PyQt4.QtGui.QApplication(sys.argv)

   # Create nodes
   n1 = boing.create("in.tuio:")
   n2 = boing.create("viz:")
   n3 = boing.create("dump:?request=$..contacts")

   # Compose the pipeline
   graph = n1 + (n2 | n3)

   # Run
   sys.exit(app.exec_())


.. rubric:: Dynamic configuration

.. todo:: Describe how to configure the pipeline dinamically

.. autofunction:: boing.activateConsole




