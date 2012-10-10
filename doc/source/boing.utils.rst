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


.. class:: StateMachine(initial=None)

   The :class:`StateMachine` class defines an object that owns a state
   defined by a :class:`collections.Mapping` type object. The argument
   *initial* can be used to define the initial state.

   .. method:: state()

      Return the current state.

   .. method:: setState(update=None, add=None, remove=None)

      Change the current state by applying *update*, *add* and
      *remove*.

   .. method:: applyDiff(diff, feedback=False)

      Apply the provided *diff* to the current state. *diff* must
      be a :class:`collections.Mapping` type containing any of the following keys:

      * ``'add'``: items that will be added to the current state;
      * ``'update'`` : items that will be update or added to the current state;
      * ``'remove'`` : items that will be removed from the current state.

      If feedback is ``True`` the diff structure between the
      previous state and the current state is provided as result of
      the method.

.. class:: Console(inputdevice, outputdevice, banner="", locals=None, parent=None)

   Interactive Python console running along the Qt eventloop.

   .. method:: push(line)

      Pass *line* to the Python interpreter.

