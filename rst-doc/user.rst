
User guide
==========

The *boing* tool enables to redirect data streams from multiple inputs
sources to multiple target outputs::

  usage: boing io [-h] [-i INPUT [INPUT ...]] [-o OUTPUT [OUTPUT ...]]
  	          [-G [URI]] [-C [HOST:PORT]] [-L LEVEL] [-T [INTEGER]] [-f]

    -i INPUT [INPUT ...]  define the inputs
    -o OUTPUT [OUTPUT ...]
			  define the outputs
    -C [HOST:PORT]        Activate console
    -G [URI]              Activate graph view (e.g. -G stdout:)
    -L LEVEL              Set logging level
    -T [INTEGER]          Set exceptions traceback depth
    -f                    Force execution (avoiding warnings)
    --version             Output version and copyright information
    -h, --help            show this help message and exit

Inputs and outputs must be defined using :doc:`URIs <uris>` .

Generic utilities examples
--------------------------

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


OSC examples
------------

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


TUIO examples
-------------

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


Multi-touch event processing
----------------------------

Filter multi-touch events to keep only the positional information::

  boing io -i in.tuio:+filter:?attr=rel_pos -o viz:

Calibrate a multi-touch source by rotating it left::

  boing io -i in.tuio:+calib:?screen=left -o viz:

Calibrate a multi-touch source by applying a 4x4 transformation matrix::

  boing io -i in.tuio:+calib:?matrix=0,-1,0,1,1,0,0,0,0,0,1,0,0,0,0,1 -o viz:


Filtering examples
------------------

Filter contacts' position of a multi-touch source using the default filter::

  boing io -i in.tuio:+filtering: -o viz:

Filter contacts' position using an exponential filter::

  boing io -i in.tuio:+filtering:/exponential/single?alpha=0.9 -o viz:

Filter only the contact speed::

  boing io -i in.tuio:+filtering:?attr=rel_speed -o viz:

Display contact's raw data and filtered data on separate windows::

  boing io -i in.tuio: -o filtering:+viz: viz:

Add noise to the contacts' position of a multi-touch source::

  boing io -i in.tuio:+filtering:/noise/numpy.random.normal(0.0,0.01) -o viz:

Add noise and then filter the contacts' position::

  boing io -i in.tuio:+filtering:/noise/numpy.random.normal(0.0,0.01)+filtering: -o viz:
