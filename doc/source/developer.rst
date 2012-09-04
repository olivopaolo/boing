========================
 |boing| for developers
========================

Developers can easily deploy pipelines by invoking the :doc:`Boing's
API <boing>` in their Python code. The function :func:`boing.create`
can be used to instantiate the pipeline's nodes. This method requires
as argument an URI expression that is used to specify the
functionality of the nodes to be created and how they are
connected. The :doc:`uris` is the same as for the command line
script. Then, the operators :code:`+` and :code:`|` can be used
compose the pipeline as explained in the section
:ref:`node-composition`.

The following code can be used as an example for creating |boing|
pipelines::

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

.. todo::
   Describe an example of functional node.

..
   Developers can also create new nodes with custom functionality by
   simply inheriting the node base classes provided by the module
   :mod:`boing.core`.
