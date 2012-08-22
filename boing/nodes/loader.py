# -*- coding: utf-8 -*-
#
# boing/nodes/loader.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import copy
import os
import sys
import logging

from PyQt4 import QtCore
import pyparsing

from boing.core import QRequest, Functor, Identity
from boing.net import bytes, json, slip, tcp, udp
from boing.nodes import encoding, ioport
from boing.nodes.multitouch import attrToRequest
from boing.net import tcp, udp
from boing.utils import assertIsInstance
from boing.utils.fileutils \
    import File, CommunicationFile, FileReader, IODevice, CommunicationDevice
from boing.utils.url import URL

# -----------------------------------------------------------------------
# URI expressions evaluation

def evaluate(operand):
    """Return the node correspondent to the URI *operand*."""
    return evaluate(operand[1:-1]) \
        if operand.startswith("'") and operand.endswith("'") \
        or operand.startswith('"') and operand.endswith('"') \
        else createSingle(operand)

def serialize(expr):
    """Return the composition node obtained from the serialization of
    the URIs detected in *expr*."""
    op1 = expr[0][0]
    op2 = expr[0][2]
    if isinstance(op1, str): op1 = evaluate(op1)
    if isinstance(op2, str): op2 = evaluate(op2)
    return op1+op2

def parallelize(expr):
    """Return the composition node obtained from the parallelization
    of the URIs detected in *expr*."""
    op1 = expr[0][0]
    op2 = expr[0][2]
    if isinstance(op1, str): op1 = evaluate(op1)
    if isinstance(op2, str): op2 = evaluate(op2)
    return op1|op2

operand = \
    pyparsing.sglQuotedString | \
    pyparsing.dblQuotedString | \
    pyparsing.Word(pyparsing.printables,
                   excludeChars=("+", "|", "(", ")"))

grammar = pyparsing.operatorPrecedence(
    operand,
    [("+", 2, pyparsing.opAssoc.RIGHT, serialize),
     ("|", 2, pyparsing.opAssoc.RIGHT, parallelize),
     ])

# -----------------------------------------------------------------------
# URI expressions evaluation

def create(expr, parent=None):
    """Create a new node from *expr*."""
    rvalue = grammar.parseString(str(expr))[0]
    if isinstance(rvalue, str):
        return createSingle(expr, parent=parent)
    else:
        rvalue.setParent(parent)
        return rvalue

def createSingle(uri, mode="", parent=None):
    """Parse *uri* to load a sigle node."""
    logger = logging.getLogger("loader")
    if not isinstance(uri, URL): uri = URL(str(uri).strip())
    if not uri.opaque and not uri.scheme and not uri.path:
        raise ValueError("Empty URI")

    # -------------------------------------------------------------------
    # CONF
    elif uri.scheme=="conf":
        import re
        assertUriModeIn(uri, mode, "")
        if uri.site or uri.fragment: raise ValueError("Invalid URI: %s"%uri)
        filepath = uri.opaque if uri.kind==URL.OPAQUE else str(uri.path)
        if not filepath: raise ValueError("filepath must be defined: %s"%uri)
        node = create(re.sub(re.compile("#.*?\n" ), "\n",
                             File(filepath).readAll().decode()))

    # -------------------------------------------------------------------
    # BRIDGES
    elif uri.scheme in ("in", "out"):
        return createSingle(
            str(uri).replace(uri.scheme, "udp" if uri.site else "file", 1),
            uri.scheme)

    elif uri.scheme.startswith("in."):
        assertUriModeIn(uri, mode, "")
        node = createSingle(lower(uri, "in"), "in")

    elif uri.scheme.startswith("out."):
        assertUriModeIn(uri, mode, "")
        node = createSingle(lower(uri, "out"), "out")

    # -------------------------------------------------------------------
    # LOGGING
    elif uri.scheme=="log":
        return createSingle(str(uri).replace("log:", "log.json.slip:", 1),
                            parent=parent)

    elif uri.scheme.startswith("log."):
        assertUriModeIn(uri, mode, "")
        scheme = uri.scheme.replace("log.", "", 1)
        if uri.kind==URL.OPAQUE or uri.site or uri.fragment: raise ValueError(
            "Invalid URI: %s"%uri)
        elif not uri.path: raise ValueError(
            "URI's path cannot be empty: %s"%uri)
        else:
            if scheme in ("json", "json.slip"):
                query = parseQuery(uri, "request", "wrap")
                assertUriQuery(uri, query)
                query.setdefault("wrap", True)
                encoder = encoding.JsonEncoder(blender=Functor.RESULTONLY,
                                               **query)
                encoder += encoding.TextEncoder()
            elif scheme in ("osc", "osc.slip",
                            "tuio", "tuio.osc", "tuio.osc.slip"):
                assertUriQuery(uri, None)
                encoder = encoding.TuioEncoder(blender=Functor.RESULTONLY) \
                    if "tuio" in uri.scheme else None
                encoder += encoding.OscEncoder(blender=Functor.RESULTONLY,
                                               wrap=True)
            else:
                raise ValueError("Unknown log encoding: %s"%uri)
            device = createSingle("slip:%s"%uri.path, "out")
            node = encoder + device

    elif uri.scheme=="play":
        return createSingle(str(uri).replace("play:", "play.json.slip:", 1),
                            parent=parent)

    elif uri.scheme.startswith("play."):
        assertUriModeIn(uri, mode, "")
        scheme = uri.scheme.replace("play.", "", 1)
        if uri.kind==URL.OPAQUE or uri.site or uri.fragment: raise ValueError(
            "Invalid URI: %s"%uri)
        elif not uri.path: raise ValueError(
            "URI's path cannot be empty: %s"%uri)
        else:
            query = parseQuery(uri, "loop", "speed", "interval", "noslip")
            assertUriQuery(uri, query)
            if scheme in ("json", "json.slip"):
                from boing.nodes.logger import FilePlayer
                decoder = \
                    slip.Decoder()+bytes.Decoder()+json.Decoder()
                player = FilePlayer(uri.path, decoder,
                                    FilePlayer.ProductSender(), **query)
                node = player + encoding.TextEncoder()
            elif scheme in ("osc", "osc.slip",
                            "tuio", "tuio.slip", "tuio.osc", "tuio.osc.slip"):
                player = encoding.OscLogPlayer(uri.path, **query)
                encoder = encoding.OscEncoder(blender=Functor.MERGE)
                oscdebug = encoding.OscDebug(blender=Functor.MERGE)
                node = player + encoder + oscdebug
                if "tuio" in uri.scheme:
                    node += encoding.TuioDecoder(blender=Functor.MERGE)
            else:
                raise ValueError("Unexpected encoding: %s"%uri)
            # FIXME: start should be triggered at outputs ready
            QtCore.QTimer.singleShot(300, player.start)

    elif uri.scheme=="rec":
        from boing.nodes.logger import Recorder
        assertUriModeIn(uri, mode, "", "out")
        query = parseQuery(uri,
                           "timelimit", "sizelimit",
                           "oversizecut", "fps", "timewarping",
                           "request")
        assertUriQuery(uri, query)
        node = Recorder(**query)
        node.start()
        node.gui.show()
        node.gui.raise_()

    elif uri.scheme=="player":
        return createSingle(str(uri).replace("player:", "player.json:", 1),
                      mode, parent)

    elif uri.scheme.startswith("player."):
        from boing.nodes.player import Player
        assertUriModeIn(uri, mode, "", "in")
        query = parseQuery(uri, "interval", "open")
        assertUriQuery(uri, query)
        scheme = uri.scheme.replace("player.", "", 1)
        if scheme in ("json", "json.slip"):
            from boing.nodes.logger import FilePlayer
            decoder = \
                slip.Decoder()+bytes.Decoder()+json.Decoder()
            player = Player(decoder, Player.ProductSender(), **query)
            player.gui().show()
            node = player + encoding.TextEncoder()
        elif scheme in ("osc", "osc.slip",
                        "tuio", "tuio.osc", "tuio.osc.slip"):
            player = Player(encoding.OscLogPlayer._Decoder(),
                            encoding.OscLogPlayer._Sender(),
                            (".osc.bz2", ".osc"), **query)
            player.gui().show()
            encoder = encoding.OscEncoder(blender=Functor.MERGE)
            oscdebug = encoding.OscDebug(blender=Functor.MERGE)
            node = player + encoder + oscdebug
            if "tuio" in scheme:
                node += encoding.TuioDecoder(blender=Functor.MERGE)
        else:
            raise ValueError("Unknown log encoding: %s"%uri)

    # -------------------------------------------------------------------
    # IO DEVICES
    elif uri.scheme=="stdin":
        assertUriModeIn(uri, mode, "in", "")
        assertUriQuery(uri, None)
        if uri.opaque or uri.path or uri.site or uri.fragment:
            raise ValueError("Invalid URI: %s"%uri)
        else:
            encoder = encoding.TextEncoder(blender=Functor.MERGE)
            reader = ioport.DataReader(CommunicationDevice(sys.stdin))
            node = reader + encoder

    elif uri.scheme=="stdout":
        assertUriModeIn(uri, mode, "out", "")
        assertUriQuery(uri, None)
        if uri.opaque or uri.path or uri.site or uri.fragment:
            raise ValueError("Invalid URI: %s"%uri)
        else:
            node = ioport.DataWriter(IODevice(sys.stdout))

    elif uri.scheme in ("", "file"):
        if uri.kind==URL.OPAQUE or uri.site or uri.fragment:
            raise ValueError("Invalid URI: %s"%uri)
        elif not uri.path:
            raise ValueError("URI's path cannot be empty: %s"%uri)
        assertUriModeIn(uri, mode, "in", "out")
        if mode=="in":
            filequery = parseQuery(uri, "uncompress")
            readerquery = parseQuery(uri, "postend")
            assertUriQuery(uri, tuple(filequery)+tuple(readerquery))
            path = str(uri.path)
            # Consider c:/tmp instead of /c:/tmp
            if sys.platform=="win32" and uri.path.absolute: path = path[1:]
            if os.path.isfile(path):
                inputfile = FileReader(uri, **filequery)
                # FIXME: start should be triggered at outputs ready
                QtCore.QTimer.singleShot(300, inputfile.start)
            else:
                inputfile = CommunicationFile(uri)
            encoder = encoding.TextEncoder(blender=Functor.MERGE) \
                if inputfile.isTextModeEnabled() \
                else encoding.TextDecoder(blender=Functor.MERGE)
            reader = ioport.DataReader(inputfile, **readerquery)
            node = reader + encoder
        elif mode=="out":
            assertUriQuery(uri, None)
            node = ioport.DataWriter(File(uri, File.WriteOnly))

    elif uri.scheme=="udp":
        assertUriModeIn(uri, mode, "in", "out")
        if uri.kind==URL.OPAQUE or uri.path or uri.fragment:
            raise ValueError("Invalid URI: %s"%uri)
        elif mode=="in":
            assertUriQuery(uri, None)
            encoder = encoding.TextDecoder(blender=Functor.MERGE)
            reader = ioport.DataReader(udp.UdpListener(uri))
            node = reader + encoder
            if uri.site.port==0: logger.info(
                "Listening at %s"%reader.inputDevice().url())
        elif mode=="out":
            query = parseQuery(uri, "writeend")
            assertUriQuery(uri, query)
            node = ioport.DataWriter(udp.UdpSender(uri), **query)

    elif uri.scheme=="tcp":
        assertUriModeIn(uri, mode, "in", "out")
        assertUriQuery(uri, None)
        if uri.kind==URL.OPAQUE or uri.path or uri.fragment:
            raise ValueError("Invalid URI: %s"%uri)
        elif mode=="in":
            encoder = encoding.TextDecoder(blender=Functor.MERGE)
            tunnel = Identity()
            server = NodeServer(uri.site.host, uri.site.port, parent=tunnel)
            if uri.site.port==0: logger.info("Listening at %s"%server.url())
            node = tunnel + encoder
        elif mode=="out":
            node = ioport.DataWriter(tcp.TcpConnection(uri))

    # -------------------------------------------------------------------
    # ENCODINGS
    # SLIP
    elif uri.scheme=="slip":
        extended = copy.copy(uri)
        extended.scheme += ".udp" if uri.site else ".file"
        logger.info(
            "No transport protocol specified in URI, assuming: %s"%extended.scheme)
        return createSingle(extended, mode, parent)

    elif uri.scheme.startswith("slip."):
        assertUriModeIn(uri, mode, "in", "out")
        loweruri = lower(uri, "slip")
        if mode=="in":
            if not uri.site and uri.site:
                loweruri.query.data.setdefault("uncompress", "")
            device = createSingle(loweruri, "in")
            decoder = encoding.SlipDecoder() # blender is fixed to  RESULTONLY
            textdecoder = encoding.TextDecoder(blender=Functor.MERGE)
            node = device + decoder + textdecoder
        elif mode=="out":
            encoder = encoding.SlipEncoder(blender=Functor.RESULTONLY)
            textdecoder = encoding.TextDecoder(blender=Functor.MERGE)
            device = createSingle(loweruri, "out")
            node = encoder + textdecoder + device

    # JSON
    elif uri.scheme=="json":
        extended = copy.copy(uri)
        extended.scheme += ".slip.file" if uri.path else ".udp"
        logger.info(
            "No transport protocol specified in URI, assuming: %s"%extended.scheme)
        return createSingle(extended, mode, parent)

    elif uri.scheme.startswith("json."):
        query = parseQuery(uri, "request", "noslip")
        loweruri = lower(uri, "json", query.keys())
        noslip = assertIsInstance(query.pop("noslip", False), bool)
        assertUriModeIn(uri, mode, "in", "out")
        if not noslip:
            if loweruri.scheme=="file":
                loweruri.scheme = "slip.%s"%loweruri.scheme
                logger.info(
                    "JSON over FILE is SLIP encoded by default (set noslip to disable)")
            if loweruri.scheme=="tcp":
                loweruri.scheme = "slip.%s"%loweruri.scheme
                logger.info(
                    "JSON over TCP is SLIP encoded by default (set noslip to disable)")
        if mode=="in":
            if "request" in query:
                raise ValueError("Unexpected query keys: 'request'")
            device = createSingle(loweruri, "in")
            decoder = encoding.JsonDecoder(blender=Functor.MERGE)
            node = device + decoder
        elif mode=="out":
            encoder = encoding.JsonEncoder(blender=Functor.RESULTONLY, **query)
            textencoder = encoding.TextEncoder(blender=Functor.MERGE)
            device = createSingle(loweruri, "out")
            node = encoder + textencoder + device

    # OSC
    elif uri.scheme=="osc":
        extended = copy.copy(uri)
        extended.scheme += ".slip.file" if uri.path else ".udp"
        logger.info(
            "No transport protocol specified in URI, assuming: %s"%extended.scheme)
        return createSingle(extended, mode, parent)

    elif uri.scheme.startswith("osc."):
        assertUriModeIn(uri, mode, "in", "out")
        query = parseQuery(uri, "rt", "noslip")
        loweruri = lower(uri, "osc", query.keys())
        noslip = assertIsInstance(query.pop("noslip", False), bool)
        if not noslip:
            if loweruri.scheme=="file":
                loweruri.scheme = "slip.%s"%loweruri.scheme
                logger.info(
                    "OSC over FILE is SLIP encoded by default (set noslip to disable)")
            if loweruri.scheme=="tcp":
                loweruri.scheme = "slip.%s"%loweruri.scheme
                logger.info(
                    "OSC over TCP is SLIP encoded by default (set noslip to disable)")
        if mode=="in":
            device = createSingle(loweruri, "in")
            decoder = encoding.OscDecoder(blender=Functor.MERGE, **query)
            oscdebug = encoding.OscDebug(blender=Functor.MERGE)
            node = device + decoder + oscdebug

        elif mode=="out":
            encoder = encoding.OscEncoder(blender=Functor.RESULTONLY, **query)
            decoder = encoding.OscDecoder(blender=Functor.MERGE)
            oscdebug = encoding.OscDebug(blender=Functor.MERGE)
            device = createSingle(loweruri, "out")
            node = encoder + decoder + oscdebug + device

    # TUIO
    elif uri.scheme=="tuio":
        extended = copy.copy(uri)
        if uri.path: extended.scheme += ".osc.slip.file"
        else:
            extended.scheme += ".osc.udp"
            if uri.site.port==0: extended.site.port = 3333
        logger.info(
            "No transport protocol specified in URI, assuming: %s"%extended.scheme)
        return createSingle(extended, mode, parent)

    elif uri.scheme.startswith("tuio."):
        assertUriModeIn(uri, mode, "in", "out")
        loweruri = lower(uri, "tuio")
        if not loweruri.scheme.startswith("osc."):
            loweruri.scheme = "osc.%s"%loweruri.scheme
        if mode=="in":
            device = createSingle(loweruri, "in")
            encoder = encoding.TuioDecoder(blender=Functor.MERGE)
            node = device + encoder
        elif mode=="out":
            if loweruri.site.host and loweruri.site.port==0:
                loweruri.site.port = 3333
            encoder = encoding.TuioEncoder(blender=Functor.RESULTONLY)
            device = createSingle(loweruri, "out")
            node = encoder + device

        '''# MT-DEV
    elif uri.scheme=="mtdev":
        if sys.platform == "linux2":
            if mode not in ("", "in"): raise ValueError(
                "Invalid mode for %s: %s"%(uri, mode))
            elif mode in ("", "in"):
                import boing.extra.mtdev
                node = boing.extra.mtdev.MtDevDevice(str(uri.path), **kwargs)
        else:
            raise ImportError(
                "'libmtdev' is not available on this platform: %s"%sys.platform)'''

    # -------------------------------------------------------------------
    # DATA PROCESSING
    elif uri.scheme=="nop":
        assertUriQuery(uri, None)
        node = Identity()

    elif uri.scheme in ("dump", "stat"):
        extended = copy.copy(uri)
        extended.scheme += ".udp" if extended.site \
            else ".file" if extended.path \
            else ".stdout"
        return createSingle(extended, mode, parent)

    elif uri.scheme.startswith("dump."):
        from boing.nodes import Dump
        assertUriModeIn(uri, mode, "", "out")
        query = parseQuery(uri,
                           "request", "src", "dest", "depth",
                           "separator", "mode")
        dump = Dump(**query) # blender is fixed to  RESULTONLY
        encoder = encoding.TextEncoder(blender=Functor.MERGE)
        device = createSingle(lower(uri, "dump", query.keys()), "out")
        node = dump + encoder + device

    elif uri.scheme.startswith("stat."):
        from boing.nodes import StatProducer
        assertUriModeIn(uri, mode, "", "out")
        query = parseQuery(uri, "request", "filter", "fps")
        stat = StatProducer(**query) # blender is fixed to  RESULTONLY
        encoder = encoding.TextEncoder(blender=Functor.MERGE)
        device = createSingle(lower(uri, "stat", query.keys()), "out")
        node = stat + encoder + device

    elif uri.scheme=="viz":
        from boing.nodes.multitouch.ContactViz import ContactViz
        assertUriModeIn(uri, mode, "", "out")
        if uri.opaque or uri.path or uri.site or uri.fragment:
            raise ValueError("Invalid URI: %s"%uri)
        else:
            query  = parseQuery(uri, "antialiasing", "fps")
            assertUriQuery(uri, query)
            node = ContactViz(**query)

    elif uri.scheme=="lag":
        from boing.nodes import Lag
        msec = int(uri.opaque) if uri.opaque else 200
        node = Lag(msec)

    elif uri.scheme=="timekeeper":
        from boing.nodes import Timekeeper
        query = parseQuery(uri, "merge", "copy", "result")
        assertUriQuery(uri, ["merge", "copy", "result"])
        node = Timekeeper(**query)

    elif uri.scheme=="edit":
        from boing.nodes import Editor
        query = parseQuery(uri)
        blender = query.pop("blender") if "blender" in query \
                         else Functor.MERGECOPY
        node = Editor(query, blender)

    elif uri.scheme=="filter":
        from boing.nodes import Filter
        uri = copy.copy(uri)
        query = parseQuery(uri, "attr")
        assertUriQuery(uri, query)
        uri.opaque = QRequest(uri.opaque) if uri.opaque else QRequest.NONE
        if "attr" in query:
            uri.opaque += attrToRequest(query["attr"]) + QRequest("diff.removed")
        node = Filter(uri.opaque)

    elif uri.scheme=="calib":
        from boing.nodes.multitouch import Calibration
        matrix = None
        query = parseQuery(uri, "matrix", "screen", "request",
                           "merge", "copy", "result", "attr")
        if "matrix" in query:
            query["matrix"] = Calibration.buildMatrix(
                tuple(map(float, query["matrix"].strip().split(","))))
        elif "screen" in query:
            screen = query.pop("screen")
            query["matrix"] = Calibration.Identity if screen=="normal" \
                else Calibration.Left if screen=="left" \
                else Calibration.Inverted if screen=="inverted" \
                else Calibration.Right if screen=="right" \
                else Calibration.Identity
        if "attr" in query:
            request = attrToRequest(query.pop("attr"))
            query["request"] = query.get("request", QRequest.NONE) + request
        elif "request" not in query:
            query["request"] = attrToRequest("rel_pos,rel_speed")
        node = Calibration(**query)

    # elif uri.scheme=="stroke":
    #     from boing.nodes.multitouch import StrokeFinder
    #     query = parseQuery(uri, "merge", "copy", "result")
    #     node = StrokeFinder(**query)

    # elif uri.scheme=="rubine":
    #     from boing.gesture import rubine
    #     from boing.nodes.multitouch import GestureRecognizer
    #     from boing.utils import QPath, quickdict
    #     query = parseQuery(uri, "merge", "copy", "result")
    #     log = File("/home/paolo/Documents/INRIA/workspace/boing/gestures/ipad-keyboard")
    #     decoder = slip.Decoder() + bytes.Decoder() + json.Decoder()
    #     data = decoder.decode(log.readAll())
    #     ql = lambda stroke: (quickdict(x=s["x"], y=s["y"], t=s["t"]) for s in stroke)
    #     l = lambda g: (QPath.get(g, "gestures.*.cls")[0],
    #                    tuple(ql(QPath.get(g, "gestures.*.stroke")[0])))
    #     data = tuple(map(l, data))
    #     recognizer = rubine.RubineRecognizer()
    #     recognizer.buildRecognizer(data)
    #     #recognizer.loadTestTemplates()
    #     node = GestureRecognizer(recognizer, **query)

    # -------------------------------------------------------------------
    # FILTERING
    elif uri.scheme=="filtering" and uri.kind==URL.GENERIC:
        from boing.nodes import DiffArgumentFunctor
        from boing.nodes.filtering import getFunctorFactory
        # Default filter is /moving/mean?winsize=5
        if not uri.path:
            uri = URL(str(uri).replace("filtering:",
                                       "filtering:/moving/mean", 1))
            uri.query.data["winsize"] = "5"
        query = parseQuery(uri, "attr", "request", "merge", "copy", "result")
        filteruri = copy.copy(uri)
        filteruri.scheme = ""
        filteruri.kind = URL.ABSOLUTE
        query["functorfactory"] = getFunctorFactory(lower(
                filteruri, "",
                ("attr", "request", "merge", "copy", "result")))
        if "attr" in query:
            request = attrToRequest(query.pop("attr"))
            query["request"] = query.get("request", QRequest.NONE) + request
        elif "request" not in query:
            query["request"] = attrToRequest("rel_pos,rel_speed")
        node = DiffArgumentFunctor(**query)

    # -------------------------------------------------------------------
    # GRAPHERS
    elif uri.scheme.startswith("grapher."):
        assertUriModeIn(uri, mode, "", "out")
        if False: #".pydot" in uri.scheme:
            from boing.extra.pydot import DotGrapherProducer
            query = parseQuery(uri, "hz", "request", "maxdepth")
            assertUriQuery(uri, query)
            grapher = DotGrapherProducer(**query)
            #encoder = encoding.TextEncoder(blender=Functor.MERGE)
            #device = createSingle(lower(uri, "grapher", query), mode="out")
            node = grapher #+ encoder + device
            node.grapher = grapher
        else:
            from boing.nodes import SimpleGrapherProducer
            query = parseQuery(uri, "hz", "request", "maxdepth")
            assertUriQuery(uri, query)
            grapher = SimpleGrapherProducer(**query)
            encoder = encoding.TextEncoder(blender=Functor.MERGE)
            device = createSingle(lower(uri, "grapher", query), mode="out")
            node = grapher + encoder + device
            node.grapher = grapher
    else:
        raise ValueError("Invalid URI: %s"%uri)

    if parent is not None: node.setParent(None)
    return node

# -------------------------------------------------------------------

class NodeServer(tcp.TcpServer):
    def __init__(self, *args, **kwargs):
        tcp.TcpServer.__init__(self, *args, **kwargs)
        self.newConnection.connect(self.__newConnection)
    def __newConnection(self):
        conn = self.nextPendingConnection()
        reader = ioport.DataReader(conn, parent=conn)
        reader.addObserver(self.parent())

# -------------------------------------------------------------------
# URI parsing support

def parseQuery(uri, *restrictions):
    """Return a dict obtained from the uri query data filtered using
    the key list restrictions. If restrictions is empty all the query
    data is preserved. The query data values are converted using the
    function '_kwstr2value'."""
    rvalue = {}
    for key, value in uri.query.data.items():
        if not restrictions or key in restrictions:
            if key=="request":
                rvalue[key] = QRequest(value)
            elif key=="merge":
                rvalue["blender"] = Functor.MERGE
            elif key=="copy":
                rvalue["blender"] = Functor.MERGECOPY
            elif key=="result":
                rvalue["blender"] = Functor.RESULTONLY
            else:
                rvalue[key] = _kwstr2value(uri.query.data[key])
    return rvalue

def _kwstr2value(string):
    """Return the value interpreted from string."""
    if string=="": rvalue = True
    elif string.lower()=="true": rvalue = True
    elif string.lower()=="false": rvalue = False
    elif string.lower()=="none": rvalue = None
    elif string.isdecimal(): rvalue = int(string)
    else:
        try:
            rvalue = float(string)
        except ValueError:
            rvalue = string
    return rvalue

def lower(uri, schemecut="", keys=tuple()):
    """Return a copy of *uri* where :
        - *schemecut* is removed from the uri scheme ;
        - all keys in *keys* are removed from the uri's query data ;"""
    rvalue = URL(str(uri))
    # Cut scheme
    if schemecut:
        rvalue.scheme = rvalue.scheme.replace("%s."%schemecut, "", 1)
    # Cut query keys
    f = lambda kw: kw[0] not in keys
    rvalue.query.data = dict(filter(f, rvalue.query.data.items()))
    return rvalue

# -------------------------------------------------------------------
# Assert utils

def assertUriQuery(uri, accepted):
    """Raises ValueError if *uri* contains query keys not in *accepted*."""
    if not isinstance(uri, URL): uri = URL(uri)
    unexpected = uri.query.data if accepted is None \
        else list(filter(lambda k: k not in accepted, uri.query.data))
    if unexpected: raise ValueError(
        "Unexpected query keys: %s"%", ".join("'%s'"%k for k in unexpected))

def assertUriModeIn(uri, mode, *valid):
    """Raises ValueError if *mode* is not in *valid*."""
    if mode not in valid: raise ValueError(
        "Invalid mode for '%s': '%s' (Try: %s)"%(
            uri, mode, ", ".join("'%s'"%i for i in valid)))
