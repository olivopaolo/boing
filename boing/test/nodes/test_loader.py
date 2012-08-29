#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# boing/test/nodes/test_loader.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import itertools
import os
import os.path
import sys
import unittest

from PyQt4 import QtGui

import boing
import boing.utils.QPath as QPath

readable = os.path.abspath(__file__)
target = os.path.abspath(os.path.normpath(
    os.path.join(os.path.split(__file__)[0], "test.txt")))
prefix = "/" if sys.platform=="win32" else ""

isInput = lambda uri: "in." in uri
isOutput = lambda uri: "out." in uri

def _addEncoding(uri, encoding, removeMode=False):
    if not removeMode:
        return uri.replace("in", "in.%s"%encoding, 1) if uri.startswith("in") \
            else uri.replace("out", "out.%s"%encoding, 1) if uri.startswith("out") \
            else "%s.%s"%(encoding, uri)
    else:
        return uri.replace("in", "%s"%encoding, 1) if uri.startswith("in") \
            else uri.replace("out", "%s"%encoding, 1) if uri.startswith("out") \
            else "%s.%s"%(encoding, uri)

uris = {
    "stdin": {
        "valid": (
            "in.stdin:",
            "stdin:",
            ),
        "invalid": (
            ("in.stdin:opaque", ValueError),
            ("in.stdin:./relative", ValueError),
            ("in.stdin:///absolute", ValueError),
            ("in.stdin://:7777", ValueError),
            ("in.stdin://[::]", ValueError),
            ("in.stdin://[::]/path", ValueError),
            ("in.stdin://[::]:7777/path", ValueError),
            ("in.stdin:?wrong=wrong", ValueError),
            ("in.stdin:#fragment", ValueError),
            )},

    "stdout": {
        "valid": (
            "out.stdout:",
            "stdout:",
            ),
        "invalid": (
            ("out.stdout:opaque", ValueError),
            ("out.stdout:./relative", ValueError),
            ("out.stdout:///absolute", ValueError),
            ("out.stdout://:7777", ValueError),
            ("out.stdout://[::]", ValueError),
            ("out.stdout://[::]/path", ValueError),
            ("out.stdout://[::]:7777/path", ValueError),
            ("out.stdout:?wrong=wrong", ValueError),
            ("out.stdout:#fragment", ValueError),
            )},

    "file": {
        "valid": (
            "in:./%s"%os.path.relpath(readable),
            "in:%s%s"%(prefix, readable),
            "in.file:./%s"%os.path.relpath(readable),
            "in.file://%s%s"%(prefix, readable),
            "in:%s%s?uncompress"%(prefix, readable),
            "in:%s%s?uncompress"%(prefix, readable),
            "in:%s%s?uncompress=False"%(prefix, readable),
            "in:%s%s?postend"%(prefix, readable),
            "in:%s%s?postend"%(prefix, readable),
            "in:%s%s?postend=False"%(prefix, readable),
            "out:./%s"%os.path.relpath(target), # relative path
            "out:%s%s"%(prefix, target), # absolute path
            "out.file:./%s"%os.path.relpath(target), # relative path
            "out.file://%s%s"%(prefix, target),
            ),
        "invalid": (
            ("in.file:opaque", ValueError),
            ("in.file:", ValueError),
            ("in.file://", ValueError),
            ("in.file:./inexistent-relative", IOError),
            ("in.file:/inexistent-absolute", IOError),
            ("in.file:///inexistent-absolute", IOError),
            ("in.file://[::]/path", ValueError),
            ("in.file://[::]:7777/path", ValueError),
            ("in.file://[::]:7777/path", ValueError),
            ("in:%s%s?wrong=wrong"%(prefix, readable), ValueError),
            ("in:%s%s?uncompress=wrong"%(prefix, readable), TypeError),
            ("in:%s%s?postend=wrong"%(prefix, readable), TypeError),
            ("in:%s%s#fragment"%(prefix, readable), ValueError),
            ("out.file:opaque", ValueError),
            ("out.file:", ValueError),
            ("out.file://", ValueError),
            ("out.file://[::]/path", ValueError),
            ("out.file://[::]:7777/path", ValueError),
            ("out.file://[::]:7777/path", ValueError),
            ("out:%s%s?wrong=wrong"%(prefix, target), ValueError),
            ("out:%s%s#fragment"%(prefix, readable), ValueError),
            )},

    "udp": {
        "valid": (
            "in.udp:",
            "in.udp://:0",
            "in.udp://:7777",
            "in.udp://[::]",
            "out.udp://[::1]:7777",
            "out.udp://[::1]:7777?writeend",
            "out.udp://[::1]:7777?writeend=False",
            ),
        "invalid": (
            ("udp:", ValueError),
            ("in.udp:opaque", ValueError),
            ("in.udp:///absolute", ValueError),
            ("in.udp://:7777/path", ValueError),
            ("in.udp://[::]/path", ValueError),
            ("in.udp://[::]:7777/path", ValueError),
            ("in.udp:./relative", ValueError),
            ("in.udp:?wrong=wrong", ValueError),
            ("in.udp:#fragment", ValueError),
            ("out.udp:", ValueError),
            ("out.udp://:7777", ValueError),
            ("out.udp://[::1]", ValueError),
            ("out.udp://:7777/path", ValueError),
            ("out.udp://[::1]/path", ValueError),
            ("out.udp://[::1]:7777/path", ValueError),
            ("out.udp:opaque", ValueError),
            ("out.udp:///absolute", ValueError),
            ("out.udp:./relative", ValueError),
            ("out.udp://[::1]:7777?wrong=wrong", ValueError),
            ("out.udp://[::1]:7777?writeend=wrong", TypeError),
            ("out.udp://[::1]:7777#fragment", ValueError),
            )},

    "tcp": {
        "valid": (
            "in.tcp:",
            "in.tcp://:0",
            "in.tcp://:7777",
            "in.tcp://[::]",
            "out.tcp://[::1]:7777",
            ),
        "invalid": (
            ("tcp:", ValueError),
            ("in.tcp:opaque", ValueError),
            ("in.tcp:///absolute", ValueError),
            ("in.tcp://:7777/path", ValueError),
            ("in.tcp://[::]/path", ValueError),
            ("in.tcp://[::]:7777/path", ValueError),
            ("in.tcp:./relative", ValueError),
            ("in.tcp:?wrong=wrong", ValueError),
            ("in.tcp:#fragment", ValueError),
            ("out.tcp:", ValueError),
            ("out.tcp://:7777", ValueError),
            ("out.tcp://[::1]", ValueError),
            ("out.tcp://:7777/path", ValueError),
            ("out.tcp://[::1]/path", ValueError),
            ("out.tcp://[::1]:7777/path", ValueError),
            ("out.tcp:opaque", ValueError),
            ("out.tcp:///absolute", ValueError),
            ("out.tcp:./relative", ValueError),
            ("out.tcp://[::1]:7777?wrong=wrong", ValueError),
            ("out.tcp://[::1]:7777#fragment", ValueError),
            )},

    "log": {
        "valid": (
            "log:./%s"%os.path.relpath(target),
            "log:%s%s"%(prefix, target),
            "log.json:%s%s"%(prefix, target),
            "log.json.slip:%s%s"%(prefix, target),
            "log.osc:%s%s"%(prefix, target),
            "log.osc.slip:%s%s"%(prefix, target),
            "log.tuio:%s%s"%(prefix, target),
            "log.tuio.osc:%s%s"%(prefix, target),
            "log.tuio.osc.slip:%s%s"%(prefix, target),
            "log://%s%s"%(prefix, target),
            "log:%s%s?request=query"%(prefix, target),
            ),
        "invalid": (
            ("log:", ValueError),
            ("log.unknow-encoding:%s%s"%(prefix, target), ValueError),
            ("log:opaque", ValueError),
            ("log://:7777", ValueError),
            ("log://[::]", ValueError),
            ("log://[::]/path", ValueError),
            ("log://[::]:7777/path", ValueError),
            ("log:%s%s?wrong=wrong"%(prefix, target), ValueError),
            ("log:%s%s#fragment"%(prefix, target), ValueError),
            ("log.stdout://%s%s"%(prefix, target), ValueError),
            ("log.stdout:", ValueError),
            )},

    "play": {
        "valid": (
            "play:./%s"%os.path.relpath(readable), # relative path
            "play:%s%s"%(prefix, readable), # absolute path
            "play:%s%s"%(prefix, readable),
            "play.json:%s%s"%(prefix, readable),
            "play.json.slip:%s%s"%(prefix, readable),
            "play.osc:%s%s"%(prefix, readable),
            "play.osc.slip:%s%s"%(prefix, readable),
            "play.tuio:%s%s"%(prefix, readable),
            "play.tuio.slip:%s%s"%(prefix, readable),
            "play.tuio.osc:%s%s"%(prefix, readable),
            "play.tuio.osc.slip:%s%s"%(prefix, readable),
            "play:%s%s?loop"%(prefix, readable),
            "play:%s%s?loop=false"%(prefix, readable),
            "play:%s%s?speed=1"%(prefix, readable),
            "play:%s%s?speed=inf"%(prefix, readable),
            "play:%s%s?speed=0"%(prefix, readable),
            "play:%s%s?interval=0"%(prefix, readable),
            "play:%s%s?interval=2000"%(prefix, readable),
            ),
        "invalid": (
            ("play:", ValueError),
            ("play:opaque", ValueError),
            ("play:./unexistent-relative", IOError),
            ("play://:7777", ValueError),
            ("play://[::]", ValueError),
            ("play://[::]/path", ValueError),
            ("play://[::]:7777/path", ValueError),
            ("play://%s%s?wrong=wrong"%(prefix, readable), ValueError),
            ("play://%s%s#fragment"%(prefix, readable), ValueError),
            ("play://%s%s?loop=wrong"%(prefix, readable), TypeError),
            ("play://%s%s?speed=wrong"%(prefix, readable), ValueError),
            ("play://%s%s?interval=wrong"%(prefix, readable), ValueError),
            ("play.stdin:", ValueError),
            ("play.stdin://%s%s"%(prefix, readable), ValueError),
            )},

    "viz": {
        "valid": (
            "viz:",
            "viz:?antialiasing",
            "viz:?fps=70",
            ),
        "invalid": (
            ("viz.stdout:", ValueError),
            ("viz:opaque", ValueError),
            ("viz:./relative", ValueError),
            ("viz://%s%s"%(prefix, target), ValueError),
            ("viz://:7777", ValueError),
            ("viz://[::]", ValueError),
            ("viz://[::]/path", ValueError),
            ("viz://[::]:7777/path", ValueError),
            ("viz:#fragment", ValueError),
            ("viz:?wrong=wrong", ValueError),
            ("viz:?antialiasing=wrong", TypeError),
            )},
    }

uris["slip"] = {
    "valid":
        tuple(_addEncoding(url, "slip") \
                  for url in itertools.chain(
                    uris["file"]["valid"],
                    uris["udp"]["valid"],
                    uris["tcp"]["valid"],
                    )),
    "invalid":
        tuple((_addEncoding(url, "slip"), exp) \
                  for url, exp in itertools.chain(
                    uris["file"]["invalid"],
                    uris["udp"]["invalid"],
                    uris["tcp"]["invalid"],
                    )),
    }

uris["pickle"] = {
    "valid":
        tuple(_addEncoding(url, "pickle") \
                  for url in itertools.chain(
                    uris["file"]["valid"],
                    uris["udp"]["valid"],
                    uris["tcp"]["valid"],
                    uris["slip"]["valid"],
                    )) + (
        "in.pickle.stdin:",
        "in.pickle:",
        "in.pickle://:7777",
        "in.pickle://[::]",
        "in.pickle://[::]:7777",
        "in.pickle://%s%s"%(prefix, readable),
        "in.pickle:?noslip",
        "in.pickle:?noslip=false",
        "out.pickle://[::1]:7777",
        "out.pickle://%s%s"%(prefix, target),
        "out.pickle.stdout:",
        "out.pickle://[::1]:7777?noslip",
        "out.pickle://[::1]:7777?noslip=false",
        "out.pickle://[::1]:7777?protocol=None",
        "out.pickle://[::1]:7777?protocol=3",
        "out.pickle://[::1]:7777?protocol=-1",
        "out.pickle://[::1]:7777?request=query",
        ),
    "invalid":
        tuple((_addEncoding(url, "pickle"), exp) \
                  for url, exp in itertools.chain(
                    uris["file"]["invalid"],
                    uris["udp"]["invalid"],
                    uris["tcp"]["invalid"],
                    uris["slip"]["invalid"],
                    )) + (
        ("pickle:", ValueError),
        ("in.pickle:opaque", ValueError),
        ("in.pickle://:7777/path", ValueError),
        ("in.pickle://[::]/path", ValueError),
        ("in.pickle://[::]:7777/path", ValueError),
        ("in.pickle:./unexistent-relative", IOError),
        ("in.pickle:?wrong=wrong", ValueError),
        ("in.pickle:?noslip=wrong", TypeError),
        ("in.pickle:?request=query", ValueError),
        ("in.pickle:?protocol=3", ValueError),
        ("out.pickle:", ValueError),
        ("out.pickle://[::1]", ValueError),
        ("out.pickle://:7777", ValueError),
        ("out.pickle://[::1]:7777?wrong=wrong", ValueError),
        ("out.pickle://[::1]:7777?noslip=wrong", TypeError),
        ("out.pickle://[::1]:7777?protocol=wrong", TypeError),
        ),
    }

uris["json"] = {
    "valid":
        tuple(_addEncoding(url, "json") \
                  for url in itertools.chain(
                    uris["file"]["valid"],
                    uris["udp"]["valid"],
                    uris["tcp"]["valid"],
                    uris["slip"]["valid"],
                    )) + (
        "in.json.stdin:",
        "in.json:",
        "in.json://:7777",
        "in.json://[::]",
        "in.json://[::]:7777",
        "in.json://%s%s"%(prefix, readable),
        "in.json:?noslip",
        "in.json:?noslip=false",
        "out.json://[::1]:7777",
        "out.json://%s%s"%(prefix, target),
        "out.json.stdout:",
        "out.json://[::1]:7777?noslip",
        "out.json://[::1]:7777?noslip=false",
        "out.json://[::1]:7777?request=query",
        ),
    "invalid":
        tuple((_addEncoding(url, "json"), exp) \
                  for url, exp in itertools.chain(
                    uris["file"]["invalid"],
                    uris["udp"]["invalid"],
                    uris["tcp"]["invalid"],
                    uris["slip"]["invalid"],
                    )) + (
        ("json:", ValueError),
        ("in.json:opaque", ValueError),
        ("in.json://:7777/path", ValueError),
        ("in.json://[::]/path", ValueError),
        ("in.json://[::]:7777/path", ValueError),
        ("in.json:./unexistent-relative", IOError),
        ("in.json:?wrong=wrong", ValueError),
        ("in.json:?noslip=wrong", TypeError),
        ("in.json:?request=query", ValueError),
        ("out.json:", ValueError),
        ("out.json://[::1]", ValueError),
        ("out.json://:7777", ValueError),
        ("out.json://[::1]:7777?wrong=wrong", ValueError),
        ("out.json://[::1]:7777?noslip=wrong", TypeError),
        ),
    }

uris["osc"] = {
    "valid":
        tuple(_addEncoding(url, "osc") \
                  for url in itertools.chain(
                    uris["file"]["valid"],
                    uris["udp"]["valid"],
                    uris["tcp"]["valid"],
                    uris["slip"]["valid"],
                    )) + (
        "in.osc.stdin:",
        "in.osc:",
        "in.osc://:7777",
        "in.osc://[::]",
        "in.osc://[::]:7777",
        "in.osc://%s%s"%(prefix, readable),
        "in.osc:?noslip",
        "in.osc:?noslip=false",
        "in.osc:?rt",
        "in.osc:?rt=false",
        "out.osc://[::1]:7777",
        "out.osc://%s%s"%(prefix, target),
        "out.osc.stdout:",
        "out.osc://[::1]:7777?noslip",
        "out.osc://[::1]:7777?noslip=false",
        "out.osc://[::1]:7777?rt",
        "out.osc://[::1]:7777?rt=false",
        ),
    "invalid":
        tuple((_addEncoding(url, "osc"), exp) \
                  for url, exp in itertools.chain(
                    uris["file"]["invalid"],
                    uris["udp"]["invalid"],
                    uris["tcp"]["invalid"],
                    uris["slip"]["invalid"],
                    )) + (
        ("osc:", ValueError),
        ("in.osc:opaque", ValueError),
        ("in.osc://:7777/path", ValueError),
        ("in.osc://[::]/path", ValueError),
        ("in.osc://[::]:7777/path", ValueError),
        ("in.osc:./unexistant-relative", IOError),
        ("in.osc:?wrong=wrong", ValueError),
        ("in.osc:?noslip=wrong", TypeError),
        ("in.osc:?rt=wrong", TypeError),
        ("out.osc:", ValueError),
        ("out.osc://[::1]", ValueError),
        ("out.osc://:7777", ValueError),
        ("out.osc://[::1]:7777?wrong=wrong", ValueError),
        ("out.osc://[::1]:7777?noslip=wrong", TypeError),
        ("out.osc://[::1]:7777?rt=wrong", TypeError),
        ),
    }


uris["tuio"] = {
    "valid":
        tuple(_addEncoding(url, "tuio") \
                  for url in itertools.chain(
                    uris["file"]["valid"],
                    uris["udp"]["valid"],
                    uris["tcp"]["valid"],
                    uris["slip"]["valid"],
                    uris["osc"]["valid"],
                    )) + (
        "in.tuio.stdin:",
        "in.tuio:",
        "in.tuio://:7777",
        "in.tuio://[::]",
        "in.tuio://[::]:7777",
        "in.tuio://%s%s"%(prefix, readable),
        "in.tuio:?rawsource",
        "in.tuio:?rawsource=false",
        "out.tuio://[::1]",
        "out.tuio://[::1]:7777",
        "out.tuio://%s%s"%(prefix, target),
        "out.tuio.stdout:",
        "out.tuio.udp://[::1]",
        "out.tuio.slip.udp://[::1]",
        "out.tuio.tcp://[::1]",
        "out.tuio.slip.tcp://[::1]",
        "out.tuio://[::1]?rawsource",
        "out.tuio://[::1]?rawsource=false",
        "out.tuio://[::1]?noslip",
        "out.tuio://[::1]?noslip=false",
        "out.tuio://%s%s?noslip"%(prefix, target),
        "out.tuio://%s%s?noslip=false"%(prefix, target),
        ),
    "invalid":
        tuple((_addEncoding(url, "tuio"), exp) \
                  for url, exp in itertools.chain(
                    uris["file"]["invalid"],
                    )) + (
        ("tuio:", ValueError),
        ("in.tuio:opaque", ValueError),
        ("in.tuio://:7777/path", ValueError),
        ("in.tuio://[::]/path", ValueError),
        ("in.tuio://[::]:7777/path", ValueError),
        ("in.tuio:./unexistent-relative", IOError),
        ("in.tuio:?rawsource=wrong", TypeError),
        ("in.tuio:?wrong=wrong", ValueError),
        ("in.tuio.osc:opaque", ValueError),
        ("in.tuio.osc://:7777/path", ValueError),
        ("in.tuio.osc://[::]/path", ValueError),
        ("in.tuio.osc://[::]:7777/path", ValueError),
        ("in.tuio.osc:./unexistant-relative", IOError),
        ("in.tuio.osc:?wrong=wrong", ValueError),
        ("out.tuio:", ValueError),
        ("out.tuio://:7777", ValueError),
        ("out.tuio://[::1]?rawsource=wrong", TypeError),
        ("out.tuio://[::1]?wrong=wrong", ValueError),
        ("out.tuio.osc:", ValueError),
        ("out.tuio.osc://:7777", ValueError),
        ("out.tuio.udp:", ValueError),
        ("out.tuio.udp://:7777", ValueError),
        ("out.tuio.udp:", ValueError),
        ("out.tuio.udp://:7777", ValueError),
        ("out.tuio.udp://:7777/path", ValueError),
        ("out.tuio.udp://[::1]/path", ValueError),
        ("out.tuio.udp://[::1]:7777/path", ValueError),
        ("out.tuio.udp:opaque", ValueError),
        ("out.tuio.udp:///path", ValueError),
        ("out.tuio.udp:./path", ValueError),
        ("out.tuio.udp://[::1]:7777?wrong=wrong", ValueError),
        ("out.tuio.udp://[::1]:7777?writeend=wrong", TypeError),
        ("out.tuio.slip.udp:", ValueError),
        ("out.tuio.slip.udp://:7777", ValueError),
        ("out.tuio.slip.udp:", ValueError),
        ("out.tuio.slip.udp://:7777", ValueError),
        ("out.tuio.slip.udp://:7777/path", ValueError),
        ("out.tuio.slip.udp://[::1]/path", ValueError),
        ("out.tuio.slip.udp://[::1]:7777/path", ValueError),
        ("out.tuio.slip.udp:opaque", ValueError),
        ("out.tuio.slip.udp:///path", ValueError),
        ("out.tuio.slip.udp:./path", ValueError),
        ("out.tuio.slip.udp://[::1]:7777?wrong=wrong", ValueError),
        ("out.tuio.slip.udp://[::1]:7777?writeend=wrong", TypeError),
        ),
    }

uris["dump"] = {
    "valid":
        tuple(_addEncoding(url, "dump", True) \
                  for url in itertools.chain(
                    filter(lambda uri: isOutput(uri), uris["file"]["valid"]),
                    filter(isOutput, uris["udp"]["valid"]),
                    filter(isOutput, uris["tcp"]["valid"]),
                    filter(isOutput, uris["slip"]["valid"]),
                    )) + (
        "dump:",
        "dump://[::1]:7777",
        "dump:?request=query",
        "dump:?src",
        "dump:?src=false",
        "dump:?dest",
        "dump:?dest=false",
        "dump:?depth=4",
        "dump:?depth=none",
        ),
    "invalid":
        tuple((_addEncoding(url, "dump", True), exp) \
                  for url, exp in itertools.chain(
                    filter(lambda t: isOutput(t[0]), uris["file"]["invalid"]),
                    filter(lambda t: isOutput(t[0]), uris["udp"]["invalid"]),
                    filter(lambda t: isOutput(t[0]), uris["tcp"]["invalid"]),
                    filter(lambda t: isOutput(t[0]), uris["slip"]["invalid"]),
                    )) + (
        ("dump:opaque", ValueError),
        ("dump://:7777", ValueError),
        ("dump://[::1]", ValueError),
        ("dump:?wrong=wrong", ValueError),
        ("dump:?src=wrong", TypeError),
        ("dump:?dest=wrong", TypeError),
        ("dump:?depth=wrong", ValueError),
        ),
    }

uris["stat"] = {
    "valid":
        tuple(_addEncoding(url, "stat", True) \
                  for url in itertools.chain(
                    filter(lambda uri: isOutput(uri), uris["file"]["valid"]),
                    filter(isOutput, uris["udp"]["valid"]),
                    filter(isOutput, uris["tcp"]["valid"]),
                    filter(isOutput, uris["slip"]["valid"]),
                    )) + (
        "stat:",
        "stat://%s%s"%(prefix, target),
        "stat://[::1]:7777",
        "stat:?request=query",
        "stat:?fps=10",
        ),
    "invalid":
        tuple((_addEncoding(url, "stat", True), exp) \
                  for url, exp in itertools.chain(
                    filter(lambda t: isOutput(t[0]), uris["file"]["invalid"]),
                    filter(lambda t: isOutput(t[0]), uris["udp"]["invalid"]),
                    filter(lambda t: isOutput(t[0]), uris["tcp"]["invalid"]),
                    filter(lambda t: isOutput(t[0]), uris["slip"]["invalid"]),
                    )) + (
        ("stat:opaque", ValueError),
        ("stat://:7777", ValueError),
        ("stat://[::1]", ValueError),
        ("stat:?wrong=wrong", ValueError),
        ("stat:?fps=wrong", ValueError),
        ),
    }

# -------------------------------------------------------------------

class LoaderTest(unittest.TestCase):
    def __init__(self, scheme, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scheme = scheme

    def setUp(self):
        self.app = QtGui.QApplication(sys.argv)

    def tearDown(self):
        if os.path.isfile(target): os.remove(target)
        self.app.exit()
        self.app = None

    def test_not_None(self):
        for uri in uris[self.scheme]["valid"]:
            self.assertIsNotNone(boing.create(uri))
        for uri, exc in uris[self.scheme]["invalid"]:
            self.assertRaises(exc, boing.create, uri)

# -------------------------------------------------------------------
# STDIN
class TestStdin(LoaderTest):
    def __init__(self, *args, **kwargs):
        super().__init__("stdin", *args, **kwargs)

# -------------------------------------------------------------------
# STDOUT
class TestStdout(LoaderTest):
    def __init__(self, *args, **kwargs):
        super().__init__("stdout", *args, **kwargs)

# -------------------------------------------------------------------
# FILE
class TestFile(LoaderTest):

    def __init__(self, *args, **kwargs):
        super().__init__("file", *args, **kwargs)

# -------------------------------------------------------------------
# UDP
class TestUdp(LoaderTest):
    def __init__(self, *args, **kwargs):
        super().__init__("udp", *args, **kwargs)

# -------------------------------------------------------------------
# TCP
class TestTcp(LoaderTest):
    def __init__(self, *args, **kwargs):
        super().__init__("tcp", *args, **kwargs)

# -------------------------------------------------------------------
# SLIP
class TestSlip(LoaderTest):
    def __init__(self, *args, **kwargs):
        super().__init__("slip", *args, **kwargs)

# -------------------------------------------------------------------
# OSC
class TestOsc(LoaderTest):
    def __init__(self, *args, **kwargs):
        super().__init__("osc", *args, **kwargs)

# -------------------------------------------------------------------
# PICKLE
class TestPickle(LoaderTest):
    def __init__(self, *args, **kwargs):
        super().__init__("pickle", *args, **kwargs)

# -------------------------------------------------------------------
# JSON
class TestJson(LoaderTest):
    def __init__(self, *args, **kwargs):
        super().__init__("json", *args, **kwargs)

# -------------------------------------------------------------------
# TUIO
class TestTuio(LoaderTest):
    def __init__(self, *args, **kwargs):
        super().__init__("tuio", *args, **kwargs)

# -------------------------------------------------------------------
# Log
class TestLog(LoaderTest):
    def __init__(self, *args, **kwargs):
        super().__init__("log", *args, **kwargs)


# -------------------------------------------------------------------
# Play
class TestPlay(LoaderTest):
    def __init__(self, *args, **kwargs):
        super().__init__("play", *args, **kwargs)

# -------------------------------------------------------------------
# Dump
class TestDump(LoaderTest):
    def __init__(self, *args, **kwargs):
        super().__init__("dump", *args, **kwargs)

# -------------------------------------------------------------------
# Stat
class TestStat(LoaderTest):
    def __init__(self, *args, **kwargs):
        super().__init__("stat", *args, **kwargs)

# -------------------------------------------------------------------
# Viz
class TestViz(LoaderTest):
    def __init__(self, *args, **kwargs):
        super().__init__("viz", *args, **kwargs)

# -------------------------------------------------------------------

def suite():
    testcases = (
        TestStdin,
        TestStdout,
        TestFile,
        TestUdp,
        TestTcp,
        TestLog,
        TestPlay,
        TestSlip,
        TestPickle,
        TestJson,
        TestOsc,
        TestTuio,
        TestDump,
        TestStat,
        TestViz,
        )
    return unittest.TestSuite(itertools.chain(
            *(map(t, filter(lambda f: f.startswith("test_"), dir(t))) \
                  for t in testcases)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
