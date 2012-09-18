==================================================
 :mod:`boing` --- Creating and managing pipelines
==================================================

.. module:: boing
   :synopsis: Creating and managing pipelines.

Developers can easily deploy Boing pipelines by invoking the toolkit's
API in their Python code. The most important element is the function
:func:`boing.create`, which is used to instantiate the nodes of
the pipeline.

.. function:: boing.create(expr, parent=None)

   Return a new node created as defined in the expression *expr*, with
   parent object *parent*. If *expr* is composed by a single URI, the
   returned object will be a new node correspondent to the provided
   URI; if *expr* is formed by an URI expression, the returned object
   will be a composed node.

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

.. rubric:: Global configuration

The attribute :attr:`boing.config` is a :class:`dict` object used to
store any global configuration variable.

.. attribute:: config

   :class:`dict` object used to store any global configuration
   variable. |boing|'s own variables:

   * ``"--no-gui"``: set to ``True`` when GUI is disabled.

.. rubric:: Dynamic configuration

.. todo:: Describe how to configure the pipeline dinamically

.. function:: boing.activateConsole(url="", locals=None, banner=None)

   Enable a Python interpreter at *url*.

   The optional *locals* argument specifies the dictionary in which
   code will be executed; it defaults to a newly created dictionary
   with key "__name__" set to "__console__" and key "__doc__" set to
   None.

   The optional *banner* argument specifies the banner to print before
   the first interaction; by default it prints a banner similar to the
   one printed by the real Python interpreter.





