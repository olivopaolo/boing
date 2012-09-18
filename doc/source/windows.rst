======================
 |boing| on Windows 7
======================

Python 3.2
==========

First download the `Python 3.2`_ binary installer and run it.

After Python has been installed, it may be useful to modify the PATH environment
variable, so that Windows can find Python binaries and scripts without
the need of specifing all the times the entire path. As an example,
the PATH variable has been set to::

  PATH = C:\Python32;C:\Python32\Scripts


.. Qt4
.. ===

.. Qt_ libraries can be downloaded from `here
.. <http://qt.nokia.com/downloads>`_. In this guide we explain how to
.. install Qt libraries only (compiled with MinGW), and not the entire Qt
.. SDK.

.. First, it is necessary to install the MinGW compiler. In order to do
.. so, use the tool mingw-get_. Download the latest version (although
.. currently designated 'alpha') and extract the files into the directory
.. C:\\MinGW.

.. Add C:\\MinGW\\bin to the *PATH* environment variable, so that from
.. the Command Prompt you can install the necessary tools, by typing::

..   mingw-get install gcc g++ mingw32-make

.. Now you can proceed to install Qt libraries using the downloaded
.. Windows installer (during the installation, it will be necessary to
.. enter the directory of the MinGW binaries). After the installer has
.. finished you can modify the *PATH* environment variable again, so that
.. Windows can find the tool *qmake*, like::

..   PATH = <...>;C:\Qt\4.7.4\bin;


PyQt4
=====

Download the PyQt4_ binary installer and run it.

.. Prior to compile PyQt, you will first need to compile and install
.. SIP_. |boing| has been tested with SIP 4.12.2 and PyQt 4.8.4, which it
.. is also available from Riverbank_. After you have finished downloading
.. the source archives, extract both of them to the Qt installation
.. directory (C:\\Qt\\4.7.4\\ in this guide).

.. Now compile and install SIP, entering into the command line prompt
.. (cmd.exe) the following commands::

..   cd C:\Qt\4.7.4\sip
..   python configure.py -p win32-g++
..   mingw32-make
..   mingw32-make install

.. The same procedure is applied for compiling PyQt::

..   cd C:\Qt\4.7.4\PyQt
..   python configure.py -p win32-g++
..   mingw32-make
..   mingw32-make install

Distribute
==========

The package Distribute_ is necessary to run the boing's installer
script. Download the file `distribute_setup.py`_ and type in a
terminal::

  cd <DOWNLOAD-DIRECTORY>
  python distribute_setup.py

numpy
=====

Download the numpy_ binary installer and run it.

pyparsing
=========

Download the source code of pyparsing_, extract the archive and type
in a terminal::

  cd <PYPARSING-DIRECTORY>
  python setup.py install


|boing|
=======

If you downloaded the binary installer you just have to launch it,
otherwise extract the source archive and type in the
terminal::

  cd <BOING-DIRECTORY>
  python setup.py install


.. _`Python 3.2`: http://python.org/download/
.. _Qt: http://qt.nokia.com/products/library/
.. _mingw-get: http://sourceforge.net/projects/mingw/files/Automated%20MinGW%20Installer/mingw-get/
.. _SIP: http://www.riverbankcomputing.co.uk/software/sip/download/
.. _PyQt4: http://www.riverbankcomputing.co.uk/software/pyqt/download/
.. _numpy: http://pypi.python.org/pypi/numpy/1.6.2
.. _pyparsing: http://pypi.python.org/pypi/pyparsing/1.5.6
.. _Distribute: http://packages.python.org/distribute/index.html
.. _distribute_setup.py: http://python-distribute.org/distribute_setup.py
