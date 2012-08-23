======================
 TUIO tutorial (TODO)
======================

.. todo:: Improve the TUIO tutorial.

..
   General documentation on TUIO can be found at http://www.tuio.org/.

   Show multi-touch events of a TUIO stream received on a UDP socket
   (default port 3333)::

     boing io -i in.tuio: -o viz:

   Record to a file a TUIO stream received on a different UDP socket::

     boing io -i in.tuio://:3334 -o log:///tmp/log

   Record a TUIO stream using a buffed recorder (with GUI), while showing it::

     boing io -i in.tuio: -o rec: viz:

   Replay a TUIO log to an TCP socket::

     boing io -i play:///tmp/log -o out.tuio.tcp://[::1]:7777

   Replay a TUIO log (at double speed and loop enabled) to an UDP socket
   and show it locally (antialised at 30 fps)::

     boing io -i "play:///tmp/log?speed=2&loop" -o out.tuio://[::1]:7777 "viz:?antialiasing&fps=30"

   Merge two TUIO streams into a single TUIO stream, then show and record it::

     boing io -i in.tuio://:3334 in.tuio://:3335 -o viz: log:///tmp/log

   Use the player (with GUI) to replay logged files an show the stored
   multi-touch events::

     boing io -i player: -o viz:

   SLIP encoding is added by default for OSC packages written or read on
   TCP sockets or files. Use the URI attribute 'noslip' to avoid default
   behaviour.
