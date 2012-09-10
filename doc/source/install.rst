====================
 Installing |boing|
====================

Download
========

You can download the current release from `here
<http://github.com/olivopaolo/boing/downloads>`_.

If you are interested to the development version, you can clone the
source repository. Open a terminal and type::

  git clone https://github.com/olivopaolo/boing

Installation
============

|boing| requires the `Python 3.2`_ interpreter (or newer) and the
PyQt4_ package (a set of Python bindings for `Nokia's Qt`_ application
framework). Moreover, it also requires the following Python packages:

- numpy_
- pyparsing_

Extensive installation instructions are available for the following
platforms:

.. toctree::
   :maxdepth: 1

* :doc:`Ubuntu <ubuntu-precise>`
* :doc:`OS X 10.7 <osx-lion>`
* :doc:`Windows 7 <windows>`

Tests
=====

After the installation has been completed, it may be useful to run the
test suite in order to verify that everything has been correctly
installed. In order to do so, type in a terminal::

  python3 setup.py test


It is also possible to test only a subset of the |boing|'s
modules::

  cd <BOING-DIRECTORY>
  python3 boing/test/run.py [MODULE [MODULE ...]]

The available modules are: :code:`core`, :code:`filtering`,
:code:`gesture`, :code:`net`, :code:`nodes`, :code:`utils`. If no
module is specified, all the available modules will be tested.

If you are interested to check the code coverage, you may use the tool
called `coverage by Ned Batchelder`_. Once the tool has been
installed, you simply have to type::

  cd <BOING-DIRECTORY>
  coverage run --source boing boing/test/run.py
  coverage report -m



.. _`Python 3.2`: http://python.org/download/
.. _PyQt4: http://www.riverbankcomputing.co.uk/software/pyqt/download/
.. _`Nokia's Qt`: http://qt.nokia.com
.. _numpy: http://numpy.scipy.org
.. _pyparsing: http://pyparsing.wikispaces.com
.. _`coverage by Ned Batchelder`: http://nedbatchelder.com/code/coverage/
