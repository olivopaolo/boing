=========================================
 :mod:`boing.utils` --- Common utilities
=========================================

.. module:: boing.utils
   :synopsis: Common utilities

The module :mod:`boing.utils` contains generic utility classes and
functions.

.. function:: assertIsInstance(obj, *valid)

   Raise TypeError if *obj* is not an instance of a class in *valid*.


.. function:: deepDump(obj, fd=sys.stdout, maxdepth=None, indent=2, end="\n", sort=True)

   Write to *fd* a textual representation of *obj*.


.. class:: Console(inputdevice, outputdevice, banner="", locals=None, parent=None)

   Interactive Python console running along the Qt eventloop.

   .. method:: push(line)

      Pass *line* to the Python interpreter.


.. rubric:: Submodules

.. toctree::
   :maxdepth: 1

   boing.utils.url

.. boing.utils.qpath
