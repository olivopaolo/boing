=========================
 |boing| on Ubuntu 11.04
=========================

It is possible to install Python 3 directly from the
standard repositories, by typing in a terminal::

  sudo apt-get install python3-dev python3-setuptools

PyQt for Python 3 is not available on the packages repositories so it
necessary to download the sources and compile them. Prior to compile
PyQt, you will first need to compile and install `SIP
<http://www.riverbankcomputing.co.uk/software/sip/download>`_. |boing|
has been tested with SIP 4.12.2 and PyQt 4.8.4, which it are both
available from `Riverbank
<http://www.riverbankcomputing.co.uk/software/pyqt/download>`_.

In order to compile SIP, type::

  sudo mv sip-4.12.4.tar.gz /opt/
  cd /opt/
  sudo tar -zxvf sip-4.12.4.tar.gz
  cd sip-4.12.4/
  sudo python3 configure.py
  sudo make
  sudo make install

The same procedure is applied for compiling PyQt::

  sudo mv PyQt-x11-gpl-4.8.5.tar.gz /opt/
  cd /opt/
  sudo tar -zxvf PyQt-x11-gpl-4.8.5.tar.gz
  cd PyQt-x11-gpl-4.8.5/
  sudo python3 configure.py
  sudo make
  sudo make install

In order to complete the installation, open a terminal and type::

  cd <BOING-DIRECTORY>
  sudo python3.2 setup.py install


Other Ubuntu releases
=====================

* :doc:`Ubuntu 12.04 <ubuntu-precise>`
