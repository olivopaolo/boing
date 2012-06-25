
Tests
=====

Run all available tests::

  cd <BOING-DIRECTORY>
  python3 setup.py test


Run tests for specific boing modules::

  python3 boing/test/run.py [MODULE [MODULE ...]]

Available modules:

* core
* gesture
* net
* nodes
* utils

If no module is specified, all modules will be tested.

