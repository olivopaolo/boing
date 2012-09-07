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
|boing| provides a set of functional nodes that enable to:

- read and decode input sources (e.g. TUIO, OSC, JSON);
- encode and forward data to target outputs (e.g. TUIO, OSC, JSON);
- record and replay the data flow;
- process gesture data (calibration, smoothing filtering, debugging, etc.);

..
   |boing| is licensed under the `GNU GPL2`_ license and it is being
   developed by `Paolo Olivo`_ and `Nicolas Roussel`_.

:doc:`Get started! <install>`

Showcase
========

.. raw:: html

   <!-- Add fancyBox main JS and CSS files -->
   <script type="text/javascript"
           src="_static/fancyBox/source/jquery.fancybox.js"></script>
   <link rel="stylesheet" type="text/css" media="screen"
         href="_static/fancyBox/source/jquery.fancybox.css" />

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
     Example of the functionality of a Boing pipeline.<br>
     <a href="introduction.html">Read more</a>
     <p id="fancyBoxLink"> Showcase created using
        <a target="_black" href="http://fancyapps.com/fancybox/">fancyBox</a>.
     </p>
   </div>

   <div id="example-title" style="display: none;">

     Concrete usage example: the toolkit is used to calibrate and
     smooth the input events of a TUIO device. At the same time,
     events are recorded so that, if something interesting happens,
     they can be logged into a file for replaying them.<br />

     <a href="firststeps.html">Read more</a>
     <p id="fancyBoxLink"> Showcase created using
        <a target="_black" href="http://fancyapps.com/fancybox/">fancyBox</a>.
     </p>
   </div>

   <div id="code-title" style="display: none;">
     Code snippet for creating a simple pipeline from your own code.<br>
     <a href="developer.html">Read more</a>
     <p id="fancyBoxLink"> Showcase created using
        <a target="_black" href="http://fancyapps.com/fancybox/">fancyBox</a>.
     </p>
   </div>

   <div id="recorder-title" style="display: none;">
     The gesture recorder tool.<br>
     <a href="functionalities.html#the-recorder-todo">Read more</a>
     <p id="fancyBoxLink"> Showcase created using
        <a target="_black" href="http://fancyapps.com/fancybox/">fancyBox</a>.
     </p>
   </div>

   <div id="player-title" style="display: none;">
     The gesture playlist player.<br>
     <a href="functionalities.html#the-player-todo">Read more</a>
     <p id="fancyBoxLink"> Showcase created using
        <a target="_black" href="http://fancyapps.com/fancybox/">fancyBox</a>.
     </p>
   </div>

   <p style="text-align: center;">
      <a style="text-decoration: none;" class="fancybox" rel="group"
         href="_static/pipeline.png" data-title-id="pipeline-title"
	 title="Example of the functionality of a Boing pipeline.">
         <img class="thumb" src="_static/pipeline-th.png">
      </a>
      <a style="text-decoration: none;" class="fancybox" rel="group"
         href="_static/example.png" data-title-id="example-title"
	 title="Concrete usage example.">
         <img class="thumb" src="_static/example-th.png">
      </a>
      <a style="text-decoration: none;" class="fancybox" rel="group"
         href="_static/code.png" data-title-id="code-title"
	 title="Code snippet for creating a simple pipeline from your own code.">
         <img class="thumb" src="_static/code-th.png">
      </a>
      <a style="text-decoration: none;" class="fancybox" rel="group"
         href="_images/recorder.png" data-title-id="recorder-title"
	 title="The gesture recorder tool.">
         <img class="thumb" src="_images/recorder.png" width="15%">
      </a>
      <a style="text-decoration: none;" class="fancybox" rel="group"
         href="_images/player.png" data-title-id="player-title"
	 title="The gesture playlist player.">
         <img class="thumb" src="_images/player.png" width="13%">
      </a>
   </p>
   <!--<p style="text-align: center; font-size: small;">
      <i>Showcase</i>
   </p>-->

.. _`Paolo Olivo`: http://www.olivopaolo.it
.. _`Nicolas Roussel`: http://interaction.lille.inria.fr/~roussel
.. _JSONPath: http://goessner.net/articles/JsonPath/
.. _`GNU GPL2`: http://www.gnu.org/licenses/gpl-2.0.txt

.. toctree::
   :hidden:

   documentation
