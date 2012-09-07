=======================
 Nodes reference table
=======================

.. role:: tn
.. role:: url
.. role:: arg
.. role:: oss

.. |S| replace:: :ref:`OSs <osstable>`
.. |M| replace:: :ref:`Mode <modestable>`

.. |subheader| raw:: html

   <tr><th class="subheader" colspan="5">

.. table::
   :class: uritable
   :name: Node URIs

   +---------------------------------------------------------------------------------------------------+
   |:tn:`Node URIs`                                                                                    |
   +---+---+----------------------------+----------------------+---------------------------------------+
   ||S|||M||Value                       |Query keys [#f2]_     |description |subheader| Data           |
   |   |   |                            |                      |Redirection                            |
   +===+===+============================+======================+=======================================+
   |LWX|I  ||inbridge|                  |                      |listen and decode data from an input   |
   |   |   |                            |                      |device                                 |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|O  ||outbridge|                 |                      |encode and forward the data to a target|
   |   |   |                            |                      |destination |subheader| Record/Replay  |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|I  ||play|                      |:arg:`loop, speed,    |replay a log file (default encoding    |
   |   |   |                            |interval`             ||pickle|)                              |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|O  ||log|                       |                      |record data to log file (default       |
   |   |   |                            |                      |encoding |pickle|)                     |
   |   |   |                            |                      |                                       |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|O  |:url:`rec:`                 |:arg:`request,        |data recorder with GUI                 |
   |   |   |                            |timelimit, sizelimit, |                                       |
   |   |   |                            |oversizecut, fps,     |                                       |
   |   |   |                            |timewarping`          |                                       |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|I  ||player|                    |:arg:`interval, open` |log files player with GUI (default     |
   |   |   |                            |                      |encoding |pickle|) |subheader| Data    |
   |   |   |                            |                      |Debug                                  |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|O  ||dump|                      |:arg:`request, mode,  |dump products to an output device      |
   |   |   |                            |separator, src, dest, |                                       |
   |   |   |                            |depth`                |                                       |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|O  ||stat|                      |:arg:`request, fps`   |print products statistics to an output |
   |   |   |                            |                      |device                                 |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|O  |:url:`viz:`                 |:arg:`antialiasing,   |display multi-touch contacts           |
   |   |   |                            |fps`                  ||subheader| Data Processing            |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|W  |:url:`nop:`                 |                      |no operation node                      |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|W  |:url:`edit:`                |:url:`merge, copy,    |apply to all the received products     |
   |   |   |                            |result, **dict`       |\**dict                                |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|W  |:url:`calib:`               |:url:`matrix, screen, |apply a 4x4 transformation matrix      |
   |   |   |                            |attr, request, merge, |                                       |
   |   |   |                            |copy, result`         |                                       |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|W  |:url:`filtering:`           |:url:`uri, attr,      |filter product data                    |
   |   |   |                            |request, merge, copy, |                                       |
   |   |   |                            |result`               |                                       |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|W  |:url:`timekeeper:`          |:url:`merge, copy,    |mark each received product with a      |
   |   |   |                            |result`               |timetag                                |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|W  |:url:`lag:[<msec>]`         |                      |add a lag to each received product     |
   +---+---+----------------------------+----------------------+---------------------------------------+

.. |inbridge| raw:: html

   <span class="url">in[.<a href="#encodings">&lt;encoding&gt;</a>]<a
   href="#input-output-devices">&lt;InputDevice&gt;</a></span>

.. |outbridge| raw:: html

   <span class="url">out[.<a href="#encodings">&lt;encoding&gt;</a>]<a
   href="#input-output-devices">&lt;OutputDevice&gt;</a></span>

.. |play| raw:: html

   <span class="url">play[.<a href="#encodings">&lt;encoding&gt;</a>]:&lt;filepath&gt;</span>

.. |log| raw:: html

   <span class="url">log[.<a href="#encodings">&lt;encoding&gt;</a>]:&lt;filepath&gt;</span>

.. |dump| raw:: html

   <span class="url">dump[.<a href="#encodings">&lt;encoding&gt;</a>]<a
   href="#input-output-devices">&lt;OutputDevice&gt;</a></span>

.. |stat| raw:: html

   <span class="url">stat[.<a href="#encodings">&lt;encoding&gt;</a>]<a
   href="#input-output-devices">&lt;OutputDevice&gt;</a></span>

.. |player| raw:: html

   <span class="url">player[.<a href="#encodings">&lt;encoding&gt;</a>]:</span>

.. |pickle| raw:: html

   <span class="url"><a href="#encodings">pickle</a></span>


Encodings
=========

.. table::
   :class: uritable
   :name: Encodings

   +---------------------------------------------------------------------------------------------------+
   |:tn:`Encodings` [#f3]_                                                                             |
   +---+---+----------------------------+----------------------+---------------------------------------+
   ||S|||M||Value                       |Query keys            | Description                           |
   +===+===+============================+======================+=======================================+
   |LWX|IO |:url:`slip`                 |                      |bytestream from/to SLIP_               |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|I  |:url:`pickle`               |:arg:`noslip`         | pickle_ to products                   |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|O  |:url:`pickle`               |:arg:`protocol,       |Products to pickle_                    |
   |   |   |                            |request, noslip`      |                                       |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|I  |:url:`json`                 |:arg:`noslip`         |JSON_ to products                      |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|O  |:url:`json`                 |:arg:`request, noslip`|products to JSON_                      |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|IO |:url:`osc`                  |:arg:`rt, noslip`     |bytestream from/to OSC_                |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|IO |:url:`tuio[.osc]`           |:arg:`rawsource`      |Multi-touch events from/to TUIO_       |
   |   |   |                            |                      |                                       |
   +---+---+----------------------------+----------------------+---------------------------------------+


Input/Output devices
====================

.. table::
   :class: uritable
   :name: Input/Output devices

   +---------------------------------------------------------------------------------------------------+
   |:tn:`Input/Output devices`                                                                         |
   +---+---+----------------------------+----------------------+---------------------------------------+
   ||S|||M|| Value                      | Query keys           | Description                           |
   +===+===+============================+======================+=======================================+
   |LWX|I  |:url:`:[stdin]`             |                      |read from standard input               |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|I  |:url:`:[stdout]`            |                      |write to standard output               |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|I  | :url:`[.file]:<filepath>`  |:arg:`uncompress,     |read from file                         |
   |   |   |                            |postend`              |                                       |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|O  | :url:`[.file]:<filepath>`  |                      |write to file                          |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|I  ||udpsocket|                 |                      |read from UDP socket                   |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|O  ||udpsocket|                 |:arg:`writeend`       |write to UDP socket                    |
   +---+---+----------------------------+----------------------+---------------------------------------+
   |LWX|IO ||tcpsocket|                 |:arg:`writeend`       |read/write on TCP socket               |
   +---+---+----------------------------+----------------------+---------------------------------------+

.. |udpsocket| raw:: html

   <span class="url">[.udp]://<a href="#hosts">&lt;host&gt;</a>:&lt;port&gt;</span>

.. |tcpsocket| raw:: html

   <span class="url">.tcp://<a href="#hosts">&lt;host&gt;</a>:&lt;port&gt;</span>

Hosts
=====

.. table::
   :class: uritable
   :name: Hosts

   +---------------------------------------------------------+
   |:tn:`Hosts`                                              |
   +---+---+------------------------+------------------------+
   ||S|||M||Value                   |Description             |
   +===+===+========================+========================+
   |LWX|I  |*empty*                 |same as IPv6 any address|
   +---+---+------------------------+------------------------+
   |LWX|I  |:url:`0.0.0.0`          |IPv4 any address        |
   +---+---+------------------------+------------------------+
   |LWX|I  |:url:`[::]`             |IPv6 any address        |
   +---+---+------------------------+------------------------+
   |LWX|IO |:url:`127.0.0.1`        |IPv4 loopback           |
   +---+---+------------------------+------------------------+
   |LWX|IO |:url:`[::1]`            |IPv6 loopback           |
   +---+---+------------------------+------------------------+
   |LWX|IO |:url:`x.x.x.x`          |specific IPv4 address   |
   +---+---+------------------------+------------------------+
   |LWX|IO |:url:`[x:x:x:x:x:x:x:x]`|specific IPv6 address   |
   +---+---+------------------------+------------------------+
   |LWX|IO |:url:`<hostname>`       |specific hostname       |
   +---+---+------------------------+------------------------+

Modes
=====

.. _modestable:
.. table::
   :class: uritable
   :name: Modes

   +---------------------------------+
   |:tn:`Modes`                      |
   +----------+----------------------+
   |Value     |Description           |
   +==========+======================+
   |I         |Input                 |
   +----------+----------------------+
   |O         |Output                |
   +----------+----------------------+
   |W         |Worker                |
   +----------+----------------------+

OS support
==========

.. _osstable:
.. table::
   :class: uritable
   :name: OS support

   +---------------------------------+
   |:tn:`OS support`                 |
   +----------+----------------------+
   |Value     |Description           |
   +==========+======================+
   |:oss:`L`  |Linux                 |
   +----------+----------------------+
   |:oss:`W`  |Windows 7 [#f1]_      |
   +----------+----------------------+
   |:oss:`X`  |OS X                  |
   +----------+----------------------+

.. rubric:: Footnotes

.. [#f1] On Windows, in order to define a file using the scheme
         ``file:`` it is necessary to place the character '/' (slash)
         before the drive letter
         (e.g. ``file:///C:/Windows/explorer.exe``).

.. [#f2] The available query keys are obtained from the union of the
         available query keys of all the uri components. As an
         example, the URI ``out.json://[::1]:7777`` is by default
         translated to ``out.json.udp://[::1]:7777``, so it owns the
         query keys of the JSON encoder (``request, filter``) and of
         the udp socket node (``writeend``).

.. [#f3] Some encodings have default input/output devices
         (e.g. ``in.tuio:`` is by default translated into
         ``in.tuio.udp://[::]:3333``).


.. _SLIP: http://www.cse.iitb.ac.in/~bestin/btech-proj/slip/x365.html
.. _pickle: http://docs.python.org/py3k/library/pickle.html
.. _JSON: http://www.json.org/
.. _OSC: http://opensoundcontrol.org/
.. _TUIO: http://www.tuio.org/
