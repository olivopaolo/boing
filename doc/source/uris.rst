=======================
 Nodes reference table
=======================

Platform

O = Mac OS X, L = Linux, W = Windows

Mode

I = Input, O = Output, F = Function

.. raw:: html

       <table style="font-size: small">
	 <tr>
	   <th colspan="2">&nbsp;</th>
	   <th>Node URIs</th>
	   <th><small>URI query keys<a href="#2"><sup>2</sup></a></small></th>
	   <th><small>Description</small></th>
	 </tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>IO</ossupport></td>
	   <td><url>&lt;in|out&gt;.[&lt;ENCODINGS&gt;.]&lt;IODEVICE&gt;</url></td>
	   <td>&nbsp;</td>
	   <td>Data bridge using custom input device and
	     decodings<a href="#4"><sup>4</sup></a></td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>I</ossupport></td>
	   <td><url>play[.&lt;ENCODING&gt;]:&lt;FILEPATH&gt;</url></td>
	   <td><url>loop, speed, interval</url></td>
	   <td>Replay data from log file (default <url>json</url>)</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>O</ossupport></td>
	   <td><url>log[.&lt;ENCODING&gt;]:&lt;FILEPATH&gt;</url></td>
	   <td>&nbsp;</td>
	   <td>Record data to log file (default encoding <url>json</url>)</td></tr>

	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>O</ossupport></td>
	   <td><url>rec:</url></td>
	   <td><url>request, timelimit, sizelimit, oversizecut, fps, timewarping
	       </url></td>
	   <td>Recorder with GUI</td></tr>

	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>I</ossupport></td>
	   <td><url>player[.&lt;ENCODING&gt;]:</url></td>
	   <td><url>interval, open</url></td>
	   <td>Open GUI player to replay data from log files (default encoding <url>json</url>)</td></tr>

	 <!-- Data Processing -->
	 <tr><th colspan="5"><small>Data Processing</small></th></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>IO</ossupport></td>
	   <td><url>nop:</url></td>
	   <td>&nbsp;</td>
	   <td>No operation node</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>O</ossupport></td>
	   <td><url>dump&lt;&lt;OUTPUT-DEVICE&gt;|:&gt;</url></td>
	   <td><url>request, mode, separator, src, dest, depth</url></td>
	   <td>Dump products to an output device (default stdout:)</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>O</ossupport></td>
	   <td><url>stat&lt;&lt;OUTPUT-DEVICE&gt;|:&gt;</url></td>
	   <td><url>request, fps</url></td>
	   <td>Print products statistics to an output device (default stdout)</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>O</ossupport></td>
	   <td><url>viz:</url></td>
	   <td><url>antialiasing, fps</url></td>
	   <td>Display multi-touch contacts</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>F</ossupport></td>
	   <td><url>filter:[&lt;QUERY&gt;]</url></td>
	   <td>attr</td>
	   <td>Discard the products that do not match 'query'</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>F</ossupport></td>
	   <td><url>edit:</url></td>
	   <td>merge, copy, result, **dict</td>
	   <td>Apply to all the received products <i>dict</i></td></tr>
	 <!-- <tr> -->
	 <!-- 	<td><ossupport>OLW</ossupport></td> -->
	 <!-- 	<td><ossupport>F</ossupport></td> -->
	 <!-- 	<td><url>filterout:[&lt;QUERY&gt;]</url></td> -->
	 <!-- 	<td>&nbsp;</td> -->
	 <!-- 	<td>Discard the products that match 'query'</td></tr> -->
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>F</ossupport></td>
	   <td><url>calib:</url></td>
	   <td><url>matrix, screen, attr, request, merge, copy, result</url></td>
	   <td>Apply a 4x4 transformation matrix</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>F</ossupport></td>
	   <td><url>filtering:</url></td>
	   <td><url>uri, attr, request, merge, copy, result</url></td>
	   <td>Filter product data using <code>filtering</code> library</td></tr>
	 <!-- Timing utils -->
	 <tr><th colspan="5"><small>Timing utils</small></th></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>F</ossupport></td>
	   <td><url>timekeeper:</url></td>
	   <td>merge, copy, result</td>
	   <td>Mark each received product with a timetag</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>F</ossupport></td>
	   <td><url>lag:[&lt;MSEC&gt;]</url></td>
	   <td>&nbsp;</td>
	   <td>Add a lag to each received product</td></tr>
	 <!-- IO devices -->
	 <tr><th colspan="5">IO devices</th></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>I</ossupport></td>
	   <td><url>stdin:</url></td>
	   <td>&nbsp;</td>
	   <td>Standard input</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>O</ossupport></td>
	   <td><url>stdout:</url></td>
	   <td>&nbsp;</td>
	   <td>Standard output</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>I</ossupport></td>
	   <td><url>&lt;ABSOLUTE-FILEPATH&gt;</url></td>
	   <td><url>uncompress, postend</url></td>
	   <td>Absolute filepath (Read Only)</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>O</ossupport></td>
	   <td><url>&lt;ABSOLUTE-FILEPATH&gt;</url></td>
	   <td>&nbsp;</td>
	   <td>Absolute filepath (Write Only)</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>I</ossupport></td>
	   <td><url>&lt;RELATIVE-FILEPATH&gt;</url></td>
	   <td><url>uncompress, postend</url></td>
	   <td>Relative filepath (Read Only)<a href="#5"><sup>5</sup></a></td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>O</ossupport></td>
	   <td><url>&lt;RELATIVE-FILEPATH&gt;</url></td>
	   <td>&nbsp;</td>
	   <td>Relative filepath (Write Only)<a href="#5"><sup>5</sup></a></td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>I</ossupport></td>
	   <td><url>udp://&lt;HOST&gt;:&lt;PORT&gt;</url></td>
	   <td>&nbsp;</td>
	   <td>Read from UDP socket</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>O</ossupport></td>
	   <td><url>udp://&lt;HOST&gt;:&lt;PORT&gt;</url></td>
	   <td><url>writeend</url></td>
	   <td>Write to UDP socket</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>IO</ossupport></td>
	   <td><url>tcp://&lt;HOST&gt;:&lt;PORT&gt;</url></td>
	   <td>&nbsp;</td>
	   <td>Read/Write on TCP socket</td></tr>

	 <!-- Encodings -->
	 <tr><th colspan="5">Encodings</th></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>IO</ossupport></td>
	   <td><url>slip</url></td>
	   <td>&nbsp;</td>
	   <td>Bytestream from/to <a href="http://www.cse.iitb.ac.in/~bestin/btech-proj/slip/x365.html">SLIP</a></td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>I</ossupport></td>
	   <td><url>pickle</url></td>
	   <td><url>noslip</url></td>
	   <td><a href="http://docs.python.org/py3k/library/pickle.html">pickle</a> to products</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>O</ossupport></td>
	   <td><url>pickle</url></td>
	   <td><url>protocol, request, noslip</url></td>
	   <td>Products to <a href="http://docs.python.org/py3k/library/pickle.html">pickle</a></td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>I</ossupport></td>
	   <td><url>json</url></td>
	   <td><url>noslip</url></td>
	   <td><a href="http://www.json.org/">JSON</a> to products</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>O</ossupport></td>
	   <td><url>json</url></td>
	   <td><url>request, noslip</url></td>
	   <td>Products to <a href="http://www.json.org/">JSON</a></td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>IO</ossupport></td>
	   <td><url>osc</url></td>
	   <td><url>rt, noslip</url></td>
	   <td>Bytestream from/to <a href="http://opensoundcontrol.org/">OSC</a></td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>IO</ossupport></td>
	   <td><url>tuio[.osc]</url></td>
	   <td><url>rawsource</url></td>
	   <td>Multi-touch events from/to <a href="http://www.tuio.org/">TUIO</a></td></tr>
	 <!-- <tr> -->
	 <!-- 	<td><ossupport>L</ossupport></td> -->
	 <!-- 	<td><ossupport>I</ossupport></td> -->
	 <!-- 	<td><url>mtdev</url></td> -->
	 <!-- 	<td>&nbsp;</td> -->
	 <!-- 	<td>Multi-touch events from <code>mtdev</code> -->
	 <!-- 	  device<a href="#6"><sup>6</sup></a></td></tr> -->
       </table>
       <br>

       <table style="font-size: small">
	 <!-- Host-->
	 <tr><th colspan="4">Host</th></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>I</ossupport></td>
	   <td><i>empty</i></td>
	   <td>same as any address IPv6</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>I</ossupport></td>
	   <td><url>0.0.0.0</url></td>
	   <td>IPv4 any address</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>I</ossupport></td>
	   <td><url>[::]</url></td>
	   <td>IPv6 any address</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>IO</ossupport></td>
	   <td><url>127.0.0.1</url></td>
	   <td>IPv4 loopback</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>IO</ossupport></td>
	   <td><url>[::1]</url></td>
	   <td>IPv6 loopback</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>IO</ossupport></td>
	   <td><url>x.x.x.x</url></td>
	   <td>specific IPv4 address</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>IO</ossupport></td>
	   <td><url>[x:x:x:x:x:x:x:x]</url></td>
	   <td>specific IPv6 address</td></tr>
	 <tr>
	   <td><ossupport>OLW</ossupport></td>
	   <td><ossupport>IO</ossupport></td>
	   <td><url>hostname</url></td>
	   <td>specific hostname</td></tr>
       </table>

       <p><a name="1"><sup>1</sup></a>On Windows, in order to define a file
	 using the scheme <url>file</url> it is necessary to place the
	 character <url>'/'</url> (slash) before the drive letter.
	 (e.g. <url>file:///C:/Windows/explorer.exe</url>)
       </p>

       <p><a name="2"><sup>2</sup></a> The available query keys are
	 obtained from the union of the available query keys of all the uri
	 components. As an example, the uri <url>out:bridge:</url> is by
	 default translated to <url>out:json.udp://[::1]:7898</url>, so it
	 owns the query keys of the json encoder (request, filter) and of
	 the udp socket node (writeend). 

       <p><a name="4"><sup>4</sup></a>Some encodings have default
	 input/output devices (e.g. <url>in:tuio:</url> is by default translated into
	 <url>in:tuio.udp://[::]:3333</url>).

       <p><a name="5"><sup>5</sup></a>It cannot be used to form composed URLs.</p>

       <!-- <p><a name="6"><sup>6</sup></a><code>mtdev</code> decoding only -->
       <!--   works on linux device files (e.g. <url>/dev/input/event6</url>).</p> -->

