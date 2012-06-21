
User guide
==========

Redirect data streams from multiple inputs to multiple outputs::

  usage: boing [-h] [-i INPUT [INPUT ...]] [-o OUTPUT [OUTPUT ...]]
  	       [-C [HOST:PORT]] [-G [URI]] [-L LEVEL] [-T [INTEGER]] [-f]
	       [--version]

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

Dump to console all the available products received from the inputs::

  boing -i stdin: -o dump:

Dump requested products to a TCP socket::

  boing -i stdin: -o dump.tcp://[::1]:7777

Dump only the products that match a query filter::

  boing -i stdin: -o dump:?request=str

Print statistics (i.e. lag, frequence, sum, tags, etc.) of the
products from two sources::

  boing -i udp://:0 tcp://:0  -o stat:

Record to a file the data coming from an UDP socket::

  boing -i udp://:0 -o log:///tmp/log

Replay a log file a forward it to a socket::

  boing -i log:///tmp/log -o stdout:

Record events using a buffed recorder (with GUI), while dumping them
to the standard output::

  boing -o rec: stdout:

OSC examples
------------

General documentation on OSC can be found at http://opensoundcontrol.org/

Examples:

Print to console decoded OSC received on a UDP socket::

  boing -i osc://:7777

Record to a file an OSC stream received on a TCP socket::

  boing -i osc.tcp://:7777 -o log:///tmp/log

Record using a buffed recorder (with GUI) an OSC stream::

  boing -i osc://:0 -o rec:

Replay an OSC log to an UDP socket::

  boing -i log:///tmp/log -o osc://[::1]:7777

Replay an OSC log (at double speed and loop enabled) to a TCP socket::

  boing -i "log:///tmp/log?speed=2&loop" -o osc.tcp://[::1]:7777


TUIO examples
-------------

General documentation on TUIO can be found at http://www.tuio.org/.

Show multi-touch events of a TUIO stream received on a UDP socket
(default port 3333)::

  boing -i tuio: -o viz:

Record to a file a TUIO stream received on a different UDP socket::

  boing -i tuio://:3334 -o log:///tmp/log

Record a TUIO stream using a buffed recorder (with GUI), while showing it::

  boing -i tuio: -o rec: viz:

Replay a TUIO log to an TCP socket::

  boing -i log:///tmp/log -o tuio.tcp://[::1]:7777

Replay a TUIO log (at double speed and loop enabled) to an UDP socket
and show it locally (antialised at 30 fps)::

  boing -i "log:///tmp/log?speed=2&loop" -o tuio://[::1]:7777 "viz:?antialiasing&fps=30"

Merge two TUIO streams into a single TUIO stream, then show and record it::

  boing -i tuio://:3334 tuio://:3335 -o viz: log:///tmp/log


SLIP encoding is added by default for OSC packages written or read on
TCP sockets or files. Use the URI attribute 'noslip' to avoid default
behaviour.


Multi-touch event processing
----------------------------

Filter multi-touch events to keep only the positional information::

  boing -i tuio:+filter:?attr=rel_pos -o viz:

Calibrate a multi-touch source by rotating it left::

  boing -i tuio:+calib:?screen=left -o viz:

Calibrate a multi-touch source by applying a 4x4 transformation matrix::

  boing -i tuio:+calib:?matrix=0,-1,0,1,1,0,0,0,0,0,1,0,0,0,0,1 -o viz:


Filtering examples
------------------

Filter contacts' position of a multi-touch source::

  boing -i tuio:?post=filtering:?uri=fltr:/moving/mean?winsize=5 -o viz:

Filter contacts' bounding box size of a multi-touch source::

  boing -i "tuio:?post='filtering:?uri=fltr:/exponential/single?alpha=0.9&attr=boundingbox.rel_size'" -o viz:

Display contact's raw data and filtered data on separate windows::

  boing -i tuio: -o viz:?pre=filtering: viz:

Add noise to the contacts' position of a multi-touch source::

  boing -i "tuio:?post=filtering:?uri=noise:numpy.random.normal(0.0,0.01)" -o viz:

Add noise to the X coordinate only of the contacts' position::

  boing -i "tuio:?post='filtering:?uri=noise:numpy.random.normal(0.0,0.03)&attr=rel_pos[0]'" -o viz:

Add noise and then filter the contacts' position::

  boing -i "tuio:?post=filtering:?uri=noise:numpy.random.normal(0.0,0.01)&post1=filtering:" -o viz:
