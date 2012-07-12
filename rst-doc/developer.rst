
Developers's guide
==================

Developers can easily deploy Boing networks writing simple Python
scripts. The method boing.create can be used to instantiate
Boing nodes. The following code can be used as a template for
instantiating a simple Boing network::

  #!/usr/bin/env python3
  import sys
  import PyQt4
  import boing

  # Init application
  app = PyQt4.QtGui.QApplication(sys.argv)

  # Create nodes
  n1 = boing.create("in.tuio:")
  n2 = boing.create("viz:")

  graph = n1 + n2

  # Run
  sys.exit(app.exec_())

.. seealso:: :doc:`uris`, :doc:`boing.create <boing>`

Package modules:

.. toctree::
   boing


