===========
 Todo list
===========

Toolkit todo
============

* *Bugs and unittest*:

  - Class :class:`DataWriter` should signal an error when it is
    demanded to write to a closed device.
  - Add :mod:`boing.test.nodes.test_loader` cases for the data
    processing nodes.
  - Add docs and unit test for class :class:`boing.utils.url.URL` on
    MS Windows.
  - Improve class :class:`QPath <boing.utils.QPath.QPath>`: regular
    expression compilation, join method, add unittest.  The command::

       QPath.filter(boing.nodes.encoding.TuioDecoder.getTemplate(), "diff.*.contacts.*.rel_pos")

    raises an error if :meth:`QPath._iterProp` returns a real
    iterator.
  - when :func:`boing.create` raises an exception, it shows the lower
    URI and not the original one. This may be misleading for users.
  - The ``player:`` 's playlist has some model trouble: when I
    drag and drop some files from a folder to the root level before
    the folder an Exception is raised. Sometimes files desappears.
  - Handle when a source has been closed and when to start players
    (e.g. if TCP socked has been disconnected, TcpServer turned off).
  - Resolve the UDP socket reuse port issue on Windows.
  - The structure ``<!...!>`` used in defining not standard
    :class:`URL <boing.utils.url.URL>` query keys and values does not
    work if characters ``#`` or ``%`` are used inside the structure.


* *Pipeline architecture*:

  - The class :class:`Producer <boing.core.Producer>` should also
    automatically know whether being active or not, like the class
    :class:`WiseWorker <boing.core.WiseWorker>` does. Check the 'tag'
    structure.
  - The class :class:`Node <boing.core.graph.Node>` shouldn't be a
    QObject?
  - Improve Graphers (Graphers should draw themselves).
  - Add exclusive requests in order to optimize productivity.


* *Data model*:

  - json and pickle decoders should someway know what they produce.
  - Check the :class:`quickdict <boing.utils.quickdict>` constructor:
    if an hierarchical dictionary is passed to the constructor not all
    the hierarchy is transformed to a quickdict.


* *Functionalities*:

  - Encoder and Decoders in module boing.nodes.encoding should inherit
    boing.nodes.Encoder and boing.node.Decoder.
  - Find a way so that the boing.node.loader can create nodes from
    external source files, so that users can add custom nodes.
  - Develop the transformation node, which transforms the data
    hierarchy (JSON-schema validator).
  - Develop ``evdev`` and ``uinput`` in&out bridges.
  - Enable remote node.
  - Improve Contact Viz.
  - Consider adding the module :mod:`libfilter.filtering.signal` to
    :mod:`boing.filtering`.
  - Develop lib tIO cython bindings.
  - When Qt4.8 will be available, add multicast support to UdpSocket.


* *Gesture Recognition*:

  - Prepare the directory with the gesture templates that the
    recognizer can use.
  - Fix the recognition nodes.
  - Support 1$ algorithm.


* *Docs*:

  - Check which Ubuntu packages are really necessary.
  - Improve docs for modules :mod:`boing.net.tcp` and
    :mod:`boing.net.udp`.

* *Other*:

  - Module :mod:`boing.utils.fileutils` should be reengineered.

Docs todo
=========

.. todolist::
