===============================
 |boing| on OS X 10.8 and 10.7
===============================

PyQt4 and Distribute
====================

If you have `Mac Ports`_, getting PyQt4_, numpy_ and Distribute_ is as
simple as typing::

  sudo port install py32-pyqt4 py32-distribute py32-numpy


|boing|
=======

In order to complete the installation, open a terminal and type::

  cd <BOING-DIRECTORY>
  sudo python3.2 setup.py install

The :command:`boing` executable may be not installed into a directory
indexed by the :code:`PATH` variable, so that it is always necessary
to use the full path to launch it. To avoid this annoying behaviour, a
simple solution is to set the installer target directory using the option
:code:`--install-scripts`. As an example::

  sudo python3.2 setup.py install --install-scripts /usr/local/bin


.. _`Mac Ports`: http://www.macports.com
.. _PyQt4: http://www.riverbankcomputing.co.uk/software/pyqt/intro
.. _numpy: http://numpy.scipy.org/

.. _Distribute: http://packages.python.org/distribute/index.html
.. _distribute_setup.py: http://python-distribute.org/distribute_setup.py
