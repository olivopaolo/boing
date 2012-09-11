==================================================
 :mod:`boing.nodes` --- The nodes of the pipeline
==================================================

.. module:: boing.nodes
   :synopsis: The nodes of the pipeline

The module :mod:`boing.nodes` contains a set of generic utility nodes.

.. rubric:: Products debugging


.. class:: Dump(request=Request.ANY, mode='items', separator='\\n\\n', src=False, dest=False, depth=None, parent=None)

   Instances of the :class:`Dump` class produce a string
   representation of the products they receive. The string is
   obtained using the function :func:`boing.utils.deepDump`.

   The parameter *request* must be an instance of the class
   :class:`boing.core.Request` and it is used to select the product
   to be dumped. The default value for request is
   :attr:`Request.ALL<boing.core.Request.ALL>`. *mode* defines how the received
   products will be dumped. The available values are:

   * ``'keys'``, only the matched keys are written;
   * ``'values'``, only the values of the matched keys are written;
   * ``'items'``, both the keys and values are written.

   *separator* defines the string to be written between two
   products. The default value for separator is ``'\n\n'``. *src*
   defines whether the node also dumps the producer of the received
   products. The default for src is False. The paramenter *dest*
   defines whether the node adds a reference to itself when it dumps
   the received products; its default value is False. The parameter
   *depth* defines how many levels of the data hierarchy are explored
   and it is directly passed to the :func:`boing.utils.deepDump`
   function.

   .. method:: mode

      Return the node's mode.

   .. method:: setMode(mode)

      Set the node's dump *mode*.

.. rubric:: Products editing


.. class:: Editor(dict, blender, parent=None)

   Instances of the :class:`Editor` class apply to the received
   products the (key, values) pairs of *dict*.

   *blender* defines the output of the node (see
   :class:`boing.core.Functor`). *parent* must be a
   :class:`PyQt4.QtCore.QObject` and it defines the node's parent.

   .. method:: get(key, default=None)

      Return the value for *key* if *key* is in the editor's
      dictionary, else *default*. If *default* is not given, it
      defaults to None.

   .. method:: set(key, value)

      Set the value for *key* to *value*.

   .. method:: items

      Return a new view of the editor dictionary's items ((key, value)
      pairs).

.. class:: DiffArgumentFunctor(functorfactory, request, blender=Functor.MERGECOPY, parent=None)

   It takes a functorfactory and for each different argument path,
   it creates a new functor which is applied to the argument
   value. The args must be a diff-based path so that functor can be
   removed depending on 'diff.removed' instances.

.. rubric:: Timing utilities

.. class:: Timekeeper(blender=Functor.MERGECOPY, parent=None)

   Instances of the :class:`Timekeeper` class tag each received
   product with the timestamp when the product is received; then they
   forward the product.

   *blender* defines the output of the node (see
   :class:`boing.core.Functor`). *parent* must be a
   :class:`PyQt4.QtCore.QObject` and it defines the node's parent.


.. class:: Lag(msec, parent=None)

   Instances of the :class:`Lag` class forward the received products
   after a delay.

   The parameter *msec* defines the lag in milliseconds. *parent* must
   be a :class:`PyQt4.QtCore.QObject` and it defines the node's
   parent.
