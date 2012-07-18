=====
Boing
=====

A flexible pipeline generator.

Introduction
============

Boing is a toolkit designed to support the development of gesture
enabled applications.

It enables to create pipelines for connecting different input sources
to multiple target destinations (e.g. applications, logs, etc.)  and
eventually process the data before being dispatched. It provides nodes
to:

- read and decode input sources (TUIO, OSC, JSON);
- encode and forward input events (TUIO, OSC, JSON);
- record and replay the data flow;
- process gesture data (calibration, smoothing filtering, etc.);
- debug and get statistics of the data flow.

Boing does not impose a specific data model; instead it exploits a
query path language (similar to JSONPath) for accessing the requested
data, so that it can fit a wider range of application domains.

Boing is licensed under the GNU GPLv2 license and it is being
developed by Paolo Olivo and Nicolas Roussel.


Installation, Documentation, Examples
=====================================

Installation instructions, tutorials and general documentation,
including an API reference can be found in the doc directory.
