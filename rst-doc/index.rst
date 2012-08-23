
==========================================
 |Boing| - A flexible multi-touch toolkit
==========================================

Welcome! This is the documentation for |boing| |release|, last updated
|today|.

|boing| is a Python 3 toolkit designed to support the development of
multi-touch and gesture enabled applications.

|boing| enables to create pipelines for connecting different input
sources to multiple target destinations (e.g. applications, logs,
etc.)  and eventually process the data before being dispatched.
|boing| provides a set of preconfigured functional nodes that enable
to:

- read and decode input sources (TUIO, OSC, JSON);
- encode and forward data to target outputs (TUIO, OSC, JSON);
- record and replay the data flow;
- process gesture data (calibration, smoothing filtering, debugging, etc.);

|boing| is licensed under the `GNU GPLv2`_ license and it is being
developed by `Paolo Olivo`_ and `Nicolas Roussel`_.

.. raw:: html

   <script type="text/javascript"
           src="_static/fancyBox/lib/jquery-1.7.2.min.js"></script>

   <!-- Add fancyBox main JS and CSS files -->
   <script type="text/javascript"
           src="_static/fancyBox/source/jquery.fancybox.js"></script>
   <link rel="stylesheet" type="text/css" media="screen"
         href="_static/fancyBox/source/jquery.fancybox.css" />

   <!-- Add my gallery CSS files -->
   <link rel="stylesheet" type="text/css" media="screen"
         href="_static/gallery.css" />

   <script type="text/javascript">
      $(document).ready(function() {
         $(".fancybox").fancybox({
            wrapCSS    : 'fancybox-custom',
            closeClick : true,

            helpers : {
	       title : {
                  type : 'inside'
               },
               overlay : {
                  css : {
                     'background-color' : '#eee'}}},

            beforeLoad: function() {
               var el, id = $(this.element).data('title-id');
               if (id) {
                  el = $('#' + id);
                  if (el.length) {
                     this.title = el.html();
                  }
               }
            }});
      });
   </script>

   <div id="pipeline-title" style="display: none;">
     Example of pipeline created using Boing.<br>
     <a href="documentation.html">Read more</a>
     <p id="fancyBoxLink"> Created using
        <a target="_black" href="http://fancyapps.com/fancybox/">fancyBox</a>.
     </p>
   </div>

   <div id="recorder-title" style="display: none;">
     Gesture recorder.<br>
     <a href="functionalities.html#the-recorder">Read more</a>
     <p id="fancyBoxLink"> Created using
        <a target="_black" href="http://fancyapps.com/fancybox/">fancyBox</a>.
     </p>
   </div>

   <div id="player-title" style="display: none;">
     Gesture playlist player.<br>
     <a href="functionalities.html#the-player">Read more</a>
     <p id="fancyBoxLink"> Created using
        <a target="_black" href="http://fancyapps.com/fancybox/">fancyBox</a>.
     </p>
   </div>

   <p style="text-align: center;">
      <a style="text-decoration: none;" class="fancybox" rel="group"
         href="_static/pipeline.png" data-title-id="pipeline-title"
	 title="Example of pipeline created using Boing.">
         <img class="thumb" src="_static/pipeline-th.png">
      </a>
      <a style="text-decoration: none;" class="fancybox" rel="group"
         href="_images/recorder.png" data-title-id="recorder-title"
	 title="Gesture recorder.">
         <img class="thumb" src="_images/recorder.png" width="15%">
      </a>
      <a style="text-decoration: none;" class="fancybox" rel="group"
         href="_images/player.png" data-title-id="player-title"
	 title="Gesture playlist player.">
         <img class="thumb" src="_images/player.png" width="13%">
      </a>
   </p>
   <p style="text-align: center; font-size: small;">
   <i>Gallery</i>
   </p>

Getting started
===============

.. toctree::
   :numbered:
   :maxdepth: 1

   download
   install
   documentation
   uris
   API/boing
   tutorials/index
   changelog
   todo

.. _`Paolo Olivo`: http://www.olivopaolo.it
.. _`Nicolas Roussel`: http://interaction.lille.inria.fr/~roussel
.. _JSONPath: http://goessner.net/articles/JsonPath/
.. _`GNU GPLv2`: http://www.gnu.org/licenses/gpl-2.0.txt
