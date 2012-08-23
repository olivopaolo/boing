==================================
 Data redirection tutorial (TODO)
==================================

.. todo:: Data redirection tutorial

..
   In this tutorial you will learn how to use the redirection
   functionalities of the |boing| toolkit.

   |boing| can communicate with the external world (e.g. devices,
   applications, storage, etc.) by reading or writing from/to files or
   sockets. Since :command:`boing` is a console script, the console
   *stdin* and *stdout* are also available targets.

   Let's start considering the simplest case: redirecting the *standard input*
   to the *standard output*. Open and terminal and type::

     boing io -i stdin: -o stdout:
