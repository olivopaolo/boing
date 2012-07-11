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

uris = \
    {"stdin":
         {"valid":
              {"in": (
                    "stdin:",
                    ),
               },
          "invalid":
              {"in": (
                    ("stdin:opaque", ValueError),
                    ("stdin:./relative", ValueError),
                    ("stdin:///absolute", ValueError),
                    ("stdin://:7777", ValueError),
                    ("stdin://[::]", ValueError),
                    ("stdin://[::]/path", ValueError),
                    ("stdin://[::]:7777/path", ValueError),
                    ("stdin:?wrong=wrong", ValueError),
                    ("stdin:#fragment", ValueError),
                    ),
               },
          },
     "stdout":
         {"valid":
              {"out": (
                    "stdout:",
                    ),
               },
          "invalid":
              {"out": (
                    ("stdout:opaque", ValueError),
                    ("stdout:./relative", ValueError),
                    ("stdout:///absolute", ValueError),
                    ("stdout://:7777", ValueError),
                    ("stdout://[::]", ValueError),
                    ("stdout://[::]/path", ValueError),
                    ("stdout://[::]:7777/path", ValueError),
                    ("stdout:?wrong=wrong", ValueError),
                    ("stdout:#fragment", ValueError),
                    ),
               },
          },
     "file":
         {"valid":
              {"in": (
                    "%s%s"%(prefix, readable),
                    "%s"%os.path.relpath(readable),
                    "file://%s%s"%(prefix, readable),
                    "%s%s?uncompress"%(prefix, readable),
                    "file://%s%s?uncompress"%(prefix, readable),
                    "file://%s%s?uncompress=False"%(prefix, readable),
                    "%s%s?postend"%(prefix, readable),
                    "file://%s%s?postend"%(prefix, readable),
                    "file://%s%s?postend=False"%(prefix, readable),
                    ),
               "out": (
                    "%s%s"%(prefix, target),
                    "%s"%os.path.relpath(target),
                    "file://%s%s"%(prefix, target),
                    ),
               },
          "invalid":
              {"in": (
                    ("file:opaque", ValueError),
                    ("file:", ValueError),
                    ("file://", ValueError),
                    ("file:./relative", ValueError),
                    ("file://[::]/path", ValueError),
                    ("file://[::]:7777/path", ValueError),
                    ("file://[::]:7777/path", ValueError),
                    ("%s%s?wrong=wrong"%(prefix, readable), ValueError),
                    ("%s%s?uncompress=wrong"%(prefix, readable), TypeError),
                    ("%s%s?postend=wrong"%(prefix, readable), TypeError),
                    ("%s%s#fragment"%(prefix, readable), ValueError),
                    ),
               "out": (
                    ("file:opaque", ValueError),
                    ("file:", ValueError),
                    ("file://", ValueError),
                    ("file:./relative", ValueError),
                    ("file://[::]/path", ValueError),
                    ("file://[::]:7777/path", ValueError),
                    ("file://[::]:7777/path", ValueError),
                    ("%s%s?wrong=wrong"%(prefix, target), ValueError),
                    ("%s%s#fragment"%(prefix, readable), ValueError),
                    ),
               },
          },
     "udp":
         {"valid":
              {"in": (
                    "udp:",
                    "udp://:0",
                    "udp://:7777",
                    "udp://[::]",
                    ),
               "out": (
                    "udp://[::1]:7777",
                    "udp://[::1]:7777?writeend",
                    "udp://[::1]:7777?writeend=False",
                    ),
               },
          "invalid":
              {"in": (
                    ("udp:opaque", ValueError),
                    ("udp:///absolute", ValueError),
                    ("udp://:7777/path", ValueError),
                    ("udp://[::]/path", ValueError),
                    ("udp://[::]:7777/path", ValueError),
                    ("udp:./relative", ValueError),
                    ("udp:?wrong=wrong", ValueError),
                    ("udp:#fragment", ValueError),
                    ),
               "out": (
                    ("udp:", ValueError),
                    ("udp://:7777", ValueError),
                    ("udp://[::1]", ValueError),
                    ("udp://:7777/path", ValueError),
                    ("udp://[::1]/path", ValueError),
                    ("udp://[::1]:7777/path", ValueError),
                    ("udp:opaque", ValueError),
                    ("udp:///absolute", ValueError),
                    ("udp:./relative", ValueError),
                    ("udp://[::1]:7777?wrong=wrong", ValueError),
                    ("udp://[::1]:7777?writeend=wrong", TypeError),
                    ("udp://[::1]:7777#fragment", ValueError),
                    ),
               },
          },
     "tcp":
         {"valid":
              {"in": (
                    "tcp:",
                    "tcp://:0",
                    "tcp://:7777",
                    "tcp://[::]",
                    ),
               "out":
                   (
                    "tcp://[::1]:7777",
                    ),
               },
          "invalid":
              {"in": (
                    ("tcp:opaque", ValueError),
                    ("tcp:///absolute", ValueError),
                    ("tcp://:7777/path", ValueError),
                    ("tcp://[::]/path", ValueError),
                    ("tcp://[::]:7777/path", ValueError),
                    ("tcp:./relative", ValueError),
                    ("tcp:?wrong=wrong", ValueError),
                    ("tcp:#fragment", ValueError),
                    ),
               "out":
                   (
                    ("tcp:", ValueError),
                    ("tcp://:7777", ValueError),
                    ("tcp://[::1]", ValueError),
                    ("tcp://:7777/path", ValueError),
                    ("tcp://[::1]/path", ValueError),
                    ("tcp://[::1]:7777/path", ValueError),
                    ("tcp:opaque", ValueError),
                    ("tcp:///absolute", ValueError),
                    ("tcp:./relative", ValueError),
                    ("tcp://[::1]:7777?wrong=wrong", ValueError),
                    ("tcp://[::1]:7777#fragment", ValueError),
                   ),
               },
          },
     "bridge":
         {"valid":
              {"in": (
                    "bridge:",
                    "bridge://:0",
                    "bridge://:7777",
                    "bridge://[::]",
                    ),
               "out": (
                    "bridge:",
                    "bridge://:7777",
                    "bridge://[::]",
                    ),
               },
          "invalid":
              {"in": (
                    ("bridge:opaque", ValueError),
                    ("bridge:///absolute", ValueError),
                    ("bridge://:7777/path", ValueError),
                    ("bridge://[::]/path", ValueError),
                    ("bridge://[::]:7777/path", ValueError),
                    ("bridge:./relative", ValueError),
                    ("bridge:?wrong=wrong", ValueError),
                    ("bridge:#fragment", ValueError),
                    ),
               "out": (
                    ("bridge:opaque", ValueError),
                    ("bridge:///absolute", ValueError),
                    ("bridge://:7777/path", ValueError),
                    ("bridge://[::1]/path", ValueError),
                    ("bridge://[::1]:7777/path", ValueError),
                    ("bridge:./relative", ValueError),
                    ("bridge://[::1]:7777?wrong=wrong", ValueError),
                    ("bridge://[::1]:7777#fragment", ValueError),
                    ),
               },
          },
     "log":
         {"valid":
              {"in": (
                    "log://%s%s"%(prefix, readable),
                    "log://%s%s?loop"%(prefix, readable),
                    "log://%s%s?loop=false"%(prefix, readable),
                    "log://%s%s?speed=1"%(prefix, readable),
                    "log://%s%s?speed=inf"%(prefix, readable),
                    "log://%s%s?speed=0"%(prefix, readable),
                    "log://%s%s?interval=0"%(prefix, readable),
                    "log://%s%s?interval=2000"%(prefix, readable),
                    ),
               "out": (
                    "log://%s%s"%(prefix, target),
                    "log://%s%s?request=query"%(prefix, target),
                    ),
               },
          "invalid":
              {"in": (
                    ("log:", ValueError),
                    ("log:opaque", ValueError),
                    ("log:./relative", ValueError),
                    ("log://:7777", ValueError),
                    ("log://[::]", ValueError),
                    ("log://[::]/path", ValueError),
                    ("log://[::]:7777/path", ValueError),
                    ("log://%s%s?wrong=wrong"%(prefix, readable), ValueError),
                    ("log://%s%s#fragment"%(prefix, readable), ValueError),
                    ("log://%s%s?loop=wrong"%(prefix, readable), TypeError),
                    ("log://%s%s?speed=wrong"%(prefix, readable), ValueError),
                    ("log://%s%s?interval=wrong"%(prefix, readable), ValueError),
                    ("log.stdin:", ValueError),
                    ("log.stdin://%s%s"%(prefix, readable), ValueError),
                    ),
               "out": (
                    ("log:", ValueError),
                    ("log:opaque", ValueError),
                    ("log:./relative", ValueError),
                    ("log://:7777", ValueError),
                    ("log://[::]", ValueError),
                    ("log://[::]/path", ValueError),
                    ("log://[::]:7777/path", ValueError),
                    ("log://%s%s?wrong=wrong"%(prefix, target), ValueError),
                    ("log://%s%s#fragment"%(prefix, target), ValueError),
                    ("log.stdout://%s%s"%(prefix, target), ValueError),
                    ("log.stdout:", ValueError),
                    ),
               },
          },
     "viz":
         {"valid":
              {"out": (
                    "viz:",
                    "viz:?antialiasing",
                    "viz:?fps=70",
                    ),
               },
          "invalid":
              {"out": (
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
                    ),
               },
          },
     }

uris["slip"] = \
    {"valid":
         {"in": list("slip.%s"%url for url in itertools.chain(
                    filter(lambda u: u.startswith("file:"),
                           uris["file"]["valid"]["in"]),
                    uris["udp"]["valid"]["in"],
                    uris["tcp"]["valid"]["in"])),
          "out": list("slip.%s"%url for url in itertools.chain(
                    filter(lambda u: u.startswith("file:"),
                           uris["file"]["valid"]["out"]),
                    uris["udp"]["valid"]["out"],
                    uris["tcp"]["valid"]["out"])),
          },
     "invalid":
         {"in": list(("slip.%s"%url, exp) for url, exp in itertools.chain(
                    filter(lambda rec: rec[0].startswith("file:"),
                           uris["file"]["invalid"]["in"]),
                    uris["udp"]["invalid"]["in"],
                    uris["tcp"]["invalid"]["in"])),
          "out": list(("slip.%s"%url, exp) for url, exp in itertools.chain(
                    filter(lambda rec: rec[0].startswith("file:"),
                           uris["file"]["invalid"]["out"]),
                    uris["udp"]["invalid"]["out"],
                    uris["tcp"]["invalid"]["out"])),
          }
     }

uris["json"] = \
    {"valid":
         {"in": list(itertools.chain(
                    ("json.%s"%url for url in \
                         filter(lambda u: u.startswith("file:"),
                                uris["file"]["valid"]["in"])),
                    ("json.%s"%url for url in uris["udp"]["valid"]["in"]),
                    ("json.%s"%url for url in uris["tcp"]["valid"]["in"]),
                    ("json.%s"%url for url in uris["slip"]["valid"]["in"]),
                    (
                        "json.stdin:",
                        "json:",
                        "json://:7777",
                        "json://[::]",
                        "json://[::]:7777",
                        "json://%s%s"%(prefix, readable),
                        "json:?noslip",
                        "json:?noslip=false",
                        ),
                    )),
          "out": list(itertools.chain(
                    ("json.%s"%url for url in \
                         filter(lambda u: u.startswith("file:"),
                                uris["file"]["valid"]["out"])),
                    ("json.%s"%url for url in uris["udp"]["valid"]["out"]),
                    ("json.%s"%url for url in uris["tcp"]["valid"]["out"]),
                    ("json.%s"%url for url in uris["slip"]["valid"]["out"]),
                    (
                        "json://[::1]:7777",
                        "json://%s%s"%(prefix, target),
                        "json.stdout:",
                        "json://[::1]:7777?noslip",
                        "json://[::1]:7777?noslip=false",
                        "json://[::1]:7777?request=query",
                        )
                    )),
          },
     "invalid":
         {"in": list(itertools.chain(
                    (("json.%s"%u, e) for u,e in uris["udp"]["invalid"]["in"]),
                    (("json.%s"%u, e) for u,e in uris["tcp"]["invalid"]["in"]),
                    (("json.%s"%u, e) for u,e in uris["slip"]["invalid"]["in"]),
                    (
                        ("json:opaque", ValueError),
                        ("json://:7777/path", ValueError),
                        ("json://[::]/path", ValueError),
                        ("json://[::]:7777/path", ValueError),
                        ("json:./relative", ValueError),
                        ("json:?wrong=wrong", ValueError),
                        ("json:?noslip=wrong", TypeError),
                        ("json:?request=query", ValueError),
                        ),
                    )),
          "out": list(itertools.chain(
                    (("json.%s"%u, e) for u,e in uris["udp"]["invalid"]["out"]),
                    (("json.%s"%u, e) for u,e in uris["tcp"]["invalid"]["out"]),
                    (("json.%s"%u, e) for u,e in uris["slip"]["invalid"]["out"]),
                    (
                        ("json:", ValueError),
                        ("json://[::1]", ValueError),
                        ("json://:7777", ValueError),
                        ("json://[::1]:7777?wrong=wrong", ValueError),
                        ("json://[::1]:7777?noslip=wrong", TypeError),
                        ),
                    )),
          },
     }

uris["osc"] = \
    {"valid":
         {"in": list(itertools.chain(
                    ("osc.%s"%url for url in \
                         filter(lambda u: u.startswith("file:"),
                                uris["file"]["valid"]["in"])),
                    ("osc.%s"%url for url in uris["udp"]["valid"]["in"]),
                    ("osc.%s"%url for url in uris["tcp"]["valid"]["in"]),
                    ("osc.%s"%url for url in uris["slip"]["valid"]["in"]),
                    (
                        "osc:",
                        "osc://:7777",
                        "osc://[::]",
                        "osc://[::]:7777",
                        "osc://%s%s"%(prefix, readable),
                        "osc.stdin:",
                        "osc:?noslip",
                        "osc:?noslip=false",
                        "osc:?rt",
                        "osc:?rt=false",
                        ),
                    )),
          "out": list(itertools.chain(
                    ("osc.%s"%url for url in \
                         filter(lambda u: u.startswith("file:"),
                                uris["file"]["valid"]["out"])),
                    ("osc.%s"%url for url in uris["udp"]["valid"]["out"]),
                    ("osc.%s"%url for url in uris["tcp"]["valid"]["out"]),
                    ("osc.%s"%url for url in uris["slip"]["valid"]["out"]),
                    (
                        "osc://[::1]:7777",
                        "osc://%s%s"%(prefix, target),
                        "osc.stdout:",
                        "osc://[::1]:7777?noslip",
                        "osc://[::1]:7777?noslip=false",
                        "osc://[::1]:7777?rt",
                        "osc://[::1]:7777?rt=false",
                        )
                    )),
          },
     "invalid":
         {"in": list(itertools.chain(
                    (("osc.%s"%u, e) for u,e in \
                         filter(lambda rec: rec[0].startswith("file:"),
                                uris["file"]["invalid"]["in"])),
                    (("osc.%s"%u, e) for u,e in uris["udp"]["invalid"]["in"]),
                    (("osc.%s"%u, e) for u,e in uris["tcp"]["invalid"]["in"]),
                    (("osc.%s"%u, e) for u,e in uris["slip"]["invalid"]["in"]),
                    (
                        ("osc:opaque", ValueError),
                        ("osc://:7777/path", ValueError),
                        ("osc://[::]/path", ValueError),
                        ("osc://[::]:7777/path", ValueError),
                        ("osc:./relative", ValueError),
                        ("osc:?wrong=wrong", ValueError),
                        ("osc:?noslip=wrong", TypeError),
                        ("osc:?rt=wrong", TypeError),
                        ),
                    )),
          "out": list(itertools.chain(
                    (("osc.%s"%u, e) for u,e in \
                         filter(lambda rec: rec[0].startswith("file:"),
                                uris["file"]["invalid"]["out"])),
                    (("osc.%s"%u, e) for u,e in uris["udp"]["invalid"]["out"]),
                    (("osc.%s"%u, e) for u,e in uris["tcp"]["invalid"]["out"]),
                    (("osc.%s"%u, e) for u,e in uris["slip"]["invalid"]["out"]),
                    (
                        ("osc:", ValueError),
                        ("osc://[::1]", ValueError),
                        ("osc://:7777", ValueError),
                        ("osc://[::1]:7777?wrong=wrong", ValueError),
                        ("osc://[::1]:7777?noslip=wrong", TypeError),
                        ("osc://[::1]:7777?rt=wrong", TypeError),
                        ),
                    )),
          },
     }

uris["tuio"] = \
    {"valid":
         {"in": list(itertools.chain(
                    ("tuio.%s"%url for url in \
                         filter(lambda u: u.startswith("file:"),
                                uris["file"]["valid"]["in"])),
                    ("tuio.%s"%url for url in uris["udp"]["valid"]["in"]),
                    ("tuio.%s"%url for url in uris["tcp"]["valid"]["in"]),
                    ("tuio.%s"%url for url in uris["slip"]["valid"]["in"]),
                    ("tuio.%s"%url for url in uris["osc"]["valid"]["in"]),
                    (
                        "tuio:",
                        "tuio://:7777",
                        "tuio://[::]",
                        "tuio://[::]:7777",
                        "tuio://%s%s"%(prefix, readable),
                        "tuio.stdin:",
                        ),
                    )),
          "out": list(itertools.chain(
                    ("tuio.%s"%url for url in \
                         filter(lambda u: u.startswith("file:"),
                                uris["file"]["valid"]["out"])),
                    ("tuio.%s"%url for url in uris["udp"]["valid"]["out"]),
                    ("tuio.%s"%url for url in uris["tcp"]["valid"]["out"]),
                    ("tuio.%s"%url for url in uris["slip"]["valid"]["out"]),
                    ("tuio.%s"%url for url in uris["osc"]["valid"]["out"]),
                    (
                        "tuio://[::1]:7777",
                        "tuio://[::1]",
                        "tuio://%s%s"%(prefix, target),
                        "tuio://[::1]",
                        "tuio.stdout:",
                        "tuio.udp://[::1]",
                        "tuio.slip.udp://[::1]",
                        "tuio.tcp://[::1]",
                        "tuio.slip.tcp://[::1]",
                        "tuio://[::1]?noslip",
                        "tuio://[::1]?noslip=false",
                        "tuio://%s%s?noslip"%(prefix, target),
                        "tuio://%s%s?noslip=false"%(prefix, target),
                        )
                    )),
          },
     "invalid":
         {"in": list(itertools.chain(
                    (("tuio.%s"%u, e) for u,e in \
                         filter(lambda rec: rec[0].startswith("file:"),
                                uris["file"]["invalid"]["in"])),
                    (("tuio.%s"%u, e) for u,e in uris["udp"]["invalid"]["in"]),
                    (("tuio.%s"%u, e) for u,e in uris["tcp"]["invalid"]["in"]),
                    (("tuio.%s"%u, e) for u,e in uris["slip"]["invalid"]["in"]),
                    (
                        ("tuio:opaque", ValueError),
                        ("tuio://:7777/path", ValueError),
                        ("tuio://[::]/path", ValueError),
                        ("tuio://[::]:7777/path", ValueError),
                        ("tuio:./relative", ValueError),
                        ("tuio:?wrong=wrong", ValueError),
                        ("tuio.osc:opaque", ValueError),
                        ("tuio.osc://:7777/path", ValueError),
                        ("tuio.osc://[::]/path", ValueError),
                        ("tuio.osc://[::]:7777/path", ValueError),
                        ("tuio.osc:./relative", ValueError),
                        ("tuio.osc:?wrong=wrong", ValueError),
                        ),
                    )),
          "out": list(itertools.chain(
                    (("tuio.%s"%u, e) for u,e in \
                         filter(lambda rec: rec[0].startswith("file:"),
                                uris["file"]["invalid"]["out"])),
                    (
                        ("tuio:", ValueError),
                        ("tuio://:7777", ValueError),
                        ("tuio://[::1]?wrong=wrong", ValueError),
                        ("tuio.osc:", ValueError),
                        ("tuio.osc://:7777", ValueError),
                        ("tuio.udp:", ValueError),
                        ("tuio.udp://:7777", ValueError),
                        ("tuio.udp:", ValueError),
                        ("tuio.udp://:7777", ValueError),
                        ("tuio.udp://:7777/path", ValueError),
                        ("tuio.udp://[::1]/path", ValueError),
                        ("tuio.udp://[::1]:7777/path", ValueError),
                        ("tuio.udp:opaque", ValueError),
                        ("tuio.udp:///absolute", ValueError),
                        ("tuio.udp:./relative", ValueError),
                        ("tuio.udp://[::1]:7777?wrong=wrong", ValueError),
                        ("tuio.udp://[::1]:7777?writeend=wrong", TypeError),
                        ("tuio.slip.udp:", ValueError),
                        ("tuio.slip.udp://:7777", ValueError),
                        ("tuio.slip.udp:", ValueError),
                        ("tuio.slip.udp://:7777", ValueError),
                        ("tuio.slip.udp://:7777/path", ValueError),
                        ("tuio.slip.udp://[::1]/path", ValueError),
                        ("tuio.slip.udp://[::1]:7777/path", ValueError),
                        ("tuio.slip.udp:opaque", ValueError),
                        ("tuio.slip.udp:///absolute", ValueError),
                        ("tuio.slip.udp:./relative", ValueError),
                        ("tuio.slip.udp://[::1]:7777?wrong=wrong", ValueError),
                        ("tuio.slip.udp://[::1]:7777?writeend=wrong", TypeError),
                    ))),
          },
     }

uris["dump"] = \
    {"valid":
         {"out": list(itertools.chain(
                    ("dump.%s"%url for url in \
                         filter(lambda u: u.startswith("file:"),
                                uris["file"]["valid"]["out"])),
                    ("dump.%s"%url for url in uris["udp"]["valid"]["out"]),
                    ("dump.%s"%url for url in uris["tcp"]["valid"]["out"]),
                    ("dump.%s"%url for url in uris["slip"]["valid"]["out"]),
                    (
                        "dump:",
                        "dump://%s%s"%(prefix, target),
                        "dump://[::1]:7777",
                        "dump:?request=query",
                        "dump:?src",
                        "dump:?src=false",
                        "dump:?dest",
                        "dump:?dest=false",
                        "dump:?depth=4",
                        "dump:?depth=none",
                        )
                    )),
          },
     "invalid":
         {"out": list(itertools.chain(
                    (("dump.%s"%u, e) for u,e in \
                         filter(lambda rec: rec[0].startswith("file:"),
                                uris["file"]["invalid"]["out"])),
                    (("dump.%s"%u, e) for u,e in uris["udp"]["invalid"]["out"]),
                    (("dump.%s"%u, e) for u,e in uris["tcp"]["invalid"]["out"]),
                    (("dump.%s"%u, e) for u,e in uris["slip"]["invalid"]["out"]),
                    (
                        ("dump:opaque", ValueError),
                        ("dump://:7777", ValueError),
                        ("dump://[::1]", ValueError),
                        ("dump:?wrong=wrong", ValueError),
                        ("dump:?src=wrong", TypeError),
                        ("dump:?dest=wrong", TypeError),
                        ("dump:?depth=wrong", ValueError),
                    ))),
          },
     }

uris["stat"] = \
    {"valid":
         {"out": list(itertools.chain(
                    ("stat.%s"%url for url in \
                         filter(lambda u: u.startswith("file:"),
                                uris["file"]["valid"]["out"])),
                    ("stat.%s"%url for url in uris["udp"]["valid"]["out"]),
                    ("stat.%s"%url for url in uris["tcp"]["valid"]["out"]),
                    ("stat.%s"%url for url in uris["slip"]["valid"]["out"]),
                    (
                        "stat:",
                        "stat://%s%s"%(prefix, target),
                        "stat://[::1]:7777",
                        "stat:?request=query",
                        "stat:?fps=10",
                        )
                    )),
          },
     "invalid":
         {"out": list(itertools.chain(
                    (("stat.%s"%u, e) for u,e in \
                         filter(lambda rec: rec[0].startswith("file:"),
                                uris["file"]["invalid"]["out"])),
                    (("stat.%s"%u, e) for u,e in uris["udp"]["invalid"]["out"]),
                    (("stat.%s"%u, e) for u,e in uris["tcp"]["invalid"]["out"]),
                    (("stat.%s"%u, e) for u,e in uris["slip"]["invalid"]["out"]),
                    (
                        ("stat:opaque", ValueError),
                        ("stat://:7777", ValueError),
                        ("stat://[::1]", ValueError),
                        ("stat:?wrong=wrong", ValueError),
                    ))),
          },
     }
# for u in QPath.get(uris, "$..valid.in"):
#     print("\n".join(u))
# print()
# for u in QPath.get(uris, "osc.valid.out"):
#     print("\n".join(u))

# -------------------------------------------------------------------

class QtTest(unittest.TestCase):
    def __init__(self, scheme, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scheme = scheme

    def setUp(self):
        self.app = QtGui.QApplication(sys.argv)

    def tearDown(self):
        if os.path.isfile(target): os.remove(target)
        self.app.exit()
        self.app = None

class InTest(QtTest):
    """Test class for urls that have only input behaviour."""
    def test_not_None(self):
        for uri in uris[self.scheme]["valid"]["in"]:
            self.assertIsNotNone(boing.create(uri, "in"))
            self.assertIsNotNone(boing.create("in:%s"%uri))
        for uri, exc in uris[self.scheme]["invalid"]["in"]:
            self.assertRaises(exc, boing.create, uri, "in")
            self.assertRaises(exc, boing.create, "in:%s"%uri)
        for uri in uris[self.scheme]["valid"]["in"]:
            self.assertRaises(ValueError, boing.create, uri, "out")
            self.assertRaises(ValueError, boing.create, "out:%s"%uri)

class OutTest(QtTest):
    """Test class for urls that have only output behaviour."""
    def test_not_None(self):
        for uri in uris[self.scheme]["valid"]["out"]:
            self.assertIsNotNone(boing.create(uri, "out"))
            self.assertIsNotNone(boing.create("out:%s"%uri))
        for uri, exc in uris[self.scheme]["invalid"]["out"]:
            self.assertRaises(exc, boing.create, uri, "out")
            self.assertRaises(exc, boing.create, "out:%s"%uri)
        for uri in uris[self.scheme]["valid"]["out"]:
            self.assertRaises(ValueError, boing.create, uri, "in")
            self.assertRaises(ValueError, boing.create, "in:%s"%uri)

class IOTest(QtTest):
    """Test class for urls that have both input and output behaviour."""
    def test_not_None(self):
        for uri in uris[self.scheme]["valid"]["in"]:
            self.assertIsNotNone(boing.create(uri, "in"))
            self.assertIsNotNone(boing.create("in:%s"%uri))
        for uri, exc in uris[self.scheme]["invalid"]["in"]:
            self.assertRaises(exc, boing.create, uri, "in")
            self.assertRaises(exc, boing.create, "in:%s"%uri)
        for uri in uris[self.scheme]["valid"]["out"]:
            self.assertIsNotNone(boing.create(uri, "out"))
            self.assertIsNotNone(boing.create("out:%s"%uri))
        for uri, exc in uris[self.scheme]["invalid"]["out"]:
            self.assertRaises(exc, boing.create, uri, "out")
            self.assertRaises(exc, boing.create, "out:%s"%uri)

# -------------------------------------------------------------------
# STDIN
class TestStdin(InTest):
    def __init__(self, *args, **kwargs):
        super().__init__("stdin", *args, **kwargs)

# -------------------------------------------------------------------
# STDOUT
class TestStdout(OutTest):
    def __init__(self, *args, **kwargs):
        super().__init__("stdout", *args, **kwargs)

# -------------------------------------------------------------------
# FILE
class TestFile(IOTest):

    def __init__(self, *args, **kwargs):
        super().__init__("file", *args, **kwargs)

# -------------------------------------------------------------------
# UDP
class TestUdp(IOTest):
    def __init__(self, *args, **kwargs):
        super().__init__("udp", *args, **kwargs)

# -------------------------------------------------------------------
# TCP
class TestTcp(IOTest):
    def __init__(self, *args, **kwargs):
        super().__init__("tcp", *args, **kwargs)

# -------------------------------------------------------------------
# SLIP
class TestSlip(IOTest):
    def __init__(self, *args, **kwargs):
        super().__init__("slip", *args, **kwargs)

# -------------------------------------------------------------------
# OSC
class TestOsc(IOTest):
    def __init__(self, *args, **kwargs):
        super().__init__("osc", *args, **kwargs)

# -------------------------------------------------------------------
# JSON
class TestJson(IOTest):
    def __init__(self, *args, **kwargs):
        super().__init__("json", *args, **kwargs)

# -------------------------------------------------------------------
# TUIO
class TestTuio(IOTest):
    def __init__(self, *args, **kwargs):
        super().__init__("tuio", *args, **kwargs)

# -------------------------------------------------------------------
# Bridge
class TestBridge(IOTest):
    def __init__(self, *args, **kwargs):
        super().__init__("bridge", *args, **kwargs)

# -------------------------------------------------------------------
# Log
class TestLog(IOTest):
    def __init__(self, *args, **kwargs):
        super().__init__("log", *args, **kwargs)

# -------------------------------------------------------------------
# Dump
class TestDump(OutTest):
    def __init__(self, *args, **kwargs):
        super().__init__("dump", *args, **kwargs)

# -------------------------------------------------------------------
# Stat
class TestStat(OutTest):
    def __init__(self, *args, **kwargs):
        super().__init__("stat", *args, **kwargs)

# -------------------------------------------------------------------
# Viz
class TestViz(OutTest):
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
        TestSlip,
        TestOsc,
        TestJson,
        TestTuio,
        # TestBridge,
        TestLog,
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
