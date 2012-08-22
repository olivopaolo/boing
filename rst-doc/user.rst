============
 User guide
============

Users can deploy |boing| pipelines in two different ways:

- using the script :command:`boing`, which is an executable
  automatically installed during the package installation;

- coding a short Python script that directly invokes the |boing|'s API.

.. TODO: Speak about the configuration language.

Command line script
-------------------


The :command:`boing` script accepts as command line argument the
configuration of the pipeline to be created. The configuration can be
specified in two different ways:

- defining the inputs and the outputs of the pipeline (command
  :command:`boing io`);
- providing a single configuration formula (command :command:`boing
  cfg`).

Inputs and outputs must be defined using :doc:`URIs <uris>` .

*io*::

   usage: boing io [-h] [-i INPUT [INPUT ...]] [-o OUTPUT [OUTPUT ...]]
		   [-G [URI]] [-C [HOST:PORT]] [-L LEVEL] [-T [INTEGER]] [-f]

   optional arguments:
     -h, --help            show this help message and exit
     -i INPUT [INPUT ...]  define the inputs
     -o OUTPUT [OUTPUT ...]
			   define the outputs
     -G [URI]              activate pipeline plot (e.g. -G out.stdout:)
     -C [HOST:PORT]        activate python console
     -L LEVEL              set logging level
     -T [INTEGER]          set exceptions traceback depth
     -f                    force execution (avoiding warnings)


*cfg*::

   usage: boing cfg [-h] [-G [URI]] [-C [HOST:PORT]] [-L LEVEL] [-T [INTEGER]]
		    [-f]
		    <expr>

   positional arguments:
     <expr>          define the pipeline configuration

   optional arguments:
     -h, --help      show this help message and exit
     -G [URI]        activate pipeline plot (e.g. -G out.stdout:)
     -C [HOST:PORT]  activate python console
     -L LEVEL        set logging level
     -T [INTEGER]    set exceptions traceback depth
     -f              force execution (avoiding warnings)

Using the URI :code:`conf:` it is also possible to load the pipeline
configuration from a file::

   boing cfg conf:./config.txt


Python developers support
-------------------------

Developers can easily deploy pipelines by invoking the :doc:`Boing's
API <API/boing>` in their Python code. The factory method
:meth:`boing.create` can be used to instantiate the pipeline's
nodes. This method requires as argument an URI that is used to specify
the functionality of the node to be created. The nodes' :doc:`URI
naming convention <uris>` is the same as for the command line
script. Then, the operators :code:`+` and :code:`|` can be used
compose the pipeline as previously explained.

The following code can be used as a template for creating a |boing|
pipeline::

   #!/usr/bin/env python3
   import sys
   import PyQt4
   import boing

   # Init application
   app = PyQt4.QtGui.QApplication(sys.argv)

   # Create nodes
   n1 = boing.create("in.tuio:")
   n2 = boing.create("viz:")
   n3 = boing.create("dump:?request=diff..rel_pos")

   # Compose the pipeline
   graph = n1 + (n2 | n3)

   # Run
   sys.exit(app.exec_())

Developers can also create new nodes with custom functionality by
simply inheriting the node base classes provided by the module
:mod:`boing.core`.

.. todo::
   Describe an example of functional node.
