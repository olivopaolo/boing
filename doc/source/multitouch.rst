=======================================
 Multi-touch utilities tutorial (TODO)
=======================================

.. todo:: multi-touch utilities tutorial.

..
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
