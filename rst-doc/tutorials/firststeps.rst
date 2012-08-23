====================
 First steps (TODO)
====================

.. todo:: first steps tutorial.

..
   Redirect the standard input to a target UDP socket::

     boing io -i stdin: -o out.udp://[::1]:7777

   Dump to console all the available products received from the inputs::

     boing io -i stdin: -o dump:

   Dump requested products to a TCP socket::

     boing io -i stdin: -o dump.tcp://[::1]:7777

   Dump only the products that match a query filter::

     boing io -i stdin: -o dump:?request=str

   Print statistics (i.e. lag, frequence, sum, tags, etc.) of the
   products from two sources::

     boing io -i in.udp://:0 in.tcp://:0  -o stat:

   Record to a file the data coming from an UDP socket::

     boing io -i in.udp://:0 -o log:///tmp/log

   Replay a log file a forward it to a socket::

     boing io -i play:///tmp/log -o stdout:

   Record events using a buffed recorder (with GUI), while dumping them
   to the standard output::

     boing io -o rec: stdout:

   Use the player (with GUI) to replay logged files to an UDP socket::

     boing io -i player: -o out.udp://[::1]:7777
