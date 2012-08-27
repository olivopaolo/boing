=====================
 OSC tutorial (TODO)
=====================

.. todo:: Improve the OSC tutorial.

..
   General documentation on OSC can be found at http://opensoundcontrol.org/

   Examples:

   Print to console decoded OSC received on a UDP socket::

     boing io -i in.osc://:7777

   Record to a file an OSC stream received on a TCP socket::

     boing io -i in.osc.tcp://:7777 -o log:///tmp/log

   Record using a buffed recorder (with GUI) an OSC stream::

     boing io -i in.osc://:0 -o rec:

   Replay an OSC log to an UDP socket::

     boing io -i play:///tmp/log -o out.osc://[::1]:7777

   Replay an OSC log (at double speed and loop enabled) to a TCP socket::

     boing io -i "play:///tmp/log?speed=2&loop" -o out.osc.tcp://[::1]:7777
