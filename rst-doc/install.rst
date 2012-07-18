====================
 Installing |boing|
====================

|boing| requires the `Python 3.2`_ interpreter (or newer) and the
`PyQt 4`_ package (a set of Python bindings for `Nokia's Qt`_
application framework). Moreover, it also requires the following
Python packages:

- numpy_
- pyparsing_

Extensive installation instructions are available for the following
platforms:

.. toctree::
   :maxdepth: 1

   Ubuntu <setup/ubuntu-precise>
   OS X 10.7 <setup/osx-lion>
   Windows 7 <setup/windows>

Tests
=====

After the installation has been completed, it may be useful to run the
test suite in order to verify that everything has been correctly
installed. In order to do so, type in a terminal::

  python3 setup.py test


It is also possible to test only a subset of the |boing|'s
modules::

  python3 boing/test/run.py [MODULE [MODULE ...]]

The available modules are: :code:`core`, :code:`filtering`,
:code:`gesture`, :code:`net`, :code:`nodes`, :code:`utils`. If no
module is specified, all the available modules will be tested.


.. _`Python 3.2`: http://python.org/download/
.. _`PyQt 4`: http://www.riverbankcomputing.co.uk/software/pyqt/download/
.. _`Nokia's Qt`: http://qt.nokia.com
.. _numpy: http://numpy.scipy.org
.. _pyparsing: http://pyparsing.wikispaces.com
