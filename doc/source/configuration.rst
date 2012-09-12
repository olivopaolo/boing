================================
 Saving pipeline configurations
================================

Sometimes it can be useful to store the configuration of the pipeline
for later reuse. Writing long configurations in a terminal may also be
quite annoying. For these reasons, Boing lets users to write the
configuration of the pipeline in a text file and then to load such
configuration using the special node ``conf:``.

As an example, consider you have finally wrote the configuration of a
pipeline for comparing the result of different smoothing filters. Now
you want to save it in a file (e.g. ``config-filters.txt``) and maybe
you want to add some comments that will help you understanding the
structure of the pipeline. The file may look like the following:

.. literalinclude:: config-filters.txt

Now, in order to run the pipeline you just have to enter the command::

   boing conf:./config-filters.txt

Quite easy, isn't it?

The node ``conf:`` is actually a composite node that contains the
pipeline defined in the configuration file. For this reason, it is
also possible to use the ``conf:`` node into another
pipeline. Consider as an example that you have a multi-touch table
sending contact information via the TUIO protocol, you found a good
smoothing filter since the input is quite noisy and you also
determined the calibration matrix to fit the touch position to the
correct screen space. You are not going to change these parameters so
you would like to consider all these elements as an atomic input
source that does not mess up a larger configuration. Thus, first you
could write the configuration of your input source into a file
(e.g. ``my-mt-table.txt``), which may look like the following:

.. literalinclude:: my-mt-table.txt

Then, you can reuse your configured input device as an atomic item in
a new pipeline. As an example, let's show the contact events using the
``viz:`` node, and at the same time use the recorder widget and
forward the contacts to an other application listening for a TUIO
source on the local port 3334. The command to run is the following::

  boing "conf:./my-mt-table.txt + (viz: | rec: | out.tuio://127.0.0.1:3334)"

As you can see, saving pipeline configurations into files can be quite
useful in different situations. Needless to say that you can also use
the ``conf:`` node inside a configuration written in a file, so that
it is possible to arrange items in a hierarchical structure.



