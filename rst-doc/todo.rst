===========
 Todo list
===========

Today or tomorrow:


This week:

- create good docs;
- update module boing.core.economy docs (After Consumer);
- well document classes in boing.core.economy.

Next week:

- Prepare the directory with the gesture templates that the recognizer can use.
- Fix the recognition nodes;
- Support 1$ algorithm;
- in json encoding, for all the things that cannot be normally
  encoded, encode the __dict__ and pass the constructor parameters.

Someday:

- find a way so that the boing.node.loader can create nodes from
  external source files, so that users can add custom nodes;
- when Sphinx will use jquery1.7, change in index.rst the jquery request;
- add the boing netcat command;
- when boing.create raises an exception, it shows the lower URI and
  not the original one. This may be misleading for users.
- Develop the transformation node, which transforms the data hierarchy
  (JSON-schema validator);
- Develop Qt applications in&out bridges;
- make the UML sequence diagram for the Producer-Consumer model;
- Enable remote node.
- Encoder and Decoders in module boing.nodes.encoding should inherit
  boing.nodes.Encoder and boing.node.Decoder.
- The playlist has some model trouble. When I drag and drop some files
  from a folder to the root level before the folder an Exception is
  raised. Sometimes files desappears.
- Check which ubuntu packages are really necessary to install boing.
- Improve Graphers (Graphers should draw themselves).
- Add methods 'addPost' and 'addPre'.
- json decoder should someway now what it produces
- Add to text, slip and json encoder the compact option
- boing.core.graph.Node shouldn't be a QObject?
- Add exclusive Request in order to optimize, then upgrade
  boing.node.Filter to remove filtered request.
- Fix OscLogPlayer: why can't it also produce data?
- Add test_loaded cases for the data processing nodes.
- Check quickdict constructor: if an hierarchical dictionary is passed
  to the constructor not all the hierarchy is transformed to a
  quickdict.
- Improve Contact Viz.
- Handle the fact that gesture events don't have a source tag nor an
  id tag.
- Handle when a source has been closed and when to start players
  (e.g. if TCP socked has been disconnected, TcpServer turned off).
- write does not send any error message.
- Handle that udp and tcp sockets can be both inputs and outputs.
- Add support for pipe between processes in test.py
- Improve QPath: regular expression compilation, join method, add
  unittest.
  QPath.filter(boing.nodes.encoding.TuioDecoder.getTemplate(),
  "diff.*.contacts.*.rel_pos") raises an error if QPath._iterProp
  return an real iterator.
- Sources should also have hz selection.
- Resolve the UDP socket reuse port issue on Windows.
- Handle lib pointing runtime exceptions in pylibpointing.
- Develop lib tIO cython bindings.
- When Qt4.8 will be available, add multicast support to UdpSocket.
- Consider adding the libfilter.filtering.signal module to boing.filtering .

Docs todo
=========

.. todolist::
