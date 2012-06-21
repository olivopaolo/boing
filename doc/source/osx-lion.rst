
Boing on OS X 10.7
==================

PyQt4
-----

In you have `Mac Ports <http://www.macports.com/>`_, getting PyQt is
as simple as typing::

  sudo port install py32-pyqt4


Distribute
----------


The package `distribute
<http://packages.python.org/distribute/index.html>`_ is necessary to
run the boing's installer (i.e. *setup.py*). Download the script
`distribute_setup.py
<http://python-distribute.org/distribute_setup.py>`_ and type in a
terminal::

  sudo python3.2 distribute_setup.py


Boing
-----

In order to complete the installation, open a terminal and type::

  cd <BOING-DIRECTORY>
  sudo python3.2 setup.py install

It may be possible that the boing script is not installed into
/usr/bin, so it cannot be directly launched from the terminal. It is
possible to set the target directory using the option
--install-scripts. As an example::

  cd <BOING-DIRECTORY>
  sudo python3.2 setup.py install --install-scripts /usr/local/bin
