# -*- coding: utf-8 -*-
#
# boing/nodes/loader.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import copy
import os
import sys
import logging

from PyQt4 import QtCore

from boing import Request, Functor, Identity
from boing.nodes import encoding, ioport
from boing.nodes.multitouch import attrToRequest
from boing.net import tcp, udp
from boing.utils import assertIsInstance
from boing.utils.fileutils \
    import File, CommunicationFile, FileReader, IODevice, CommunicationDevice
from boing.utils.url import URL

def create(uri, mode="", logger=None, parent=None):
    """Create a new node from *uri*."""    
    logger = logger if logger is not None else logging.getLogger("loader")
    if not isinstance(uri, URL): uri = URL(str(uri))
    if not uri.opaque and not uri.scheme and not uri.path: 
        raise ValueError("Empty URI")

    # -------------------------------------------------------------------
    # IN: AND  OUT: REPLACED USING MODE
    if uri.scheme=="in":
        assertUriModeIn(uri, mode, "", "in")
        return create(str(uri).replace("in:", "", 1), "in", logger, parent)

    elif uri.scheme=="out":
        assertUriModeIn(uri, mode, "", "out")
        return create(str(uri).replace("out:", "", 1), "out", logger, parent)

    # -------------------------------------------------------------------
    # LOGGING

    elif uri.scheme=="log":
        return create(str(uri).replace("log:", "log.json:", 1), 
                      mode, logger, parent)

    elif uri.scheme.startswith("log."):
        assertUriModeIn(uri, mode, "in", "out")
        scheme = uri.scheme.replace("log.", "", 1)
        if uri.kind==URL.OPAQUE or uri.site or uri.fragment: raise ValueError(
            "Invalid URI: %s"%uri)
        elif not uri.path: raise ValueError(
            "URI's path cannot be empty: %s"%uri)
        elif mode=="in":
            query = parseQuery(uri, "loop", "speed", "interval", "noslip")
            assertUriQuery(uri, query)
            if scheme in ("json", "json.slip"):
                player = encoding.JsonLogPlayer(uri.path, **query)
                node = player + encoding.TextEncoder()
            elif scheme in ("osc", "osc.slip",
                            "tuio", "tuio.osc", "tuio.osc.slip"):
                player = encoding.OscLogPlayer(uri.path, **query)
                node = player + encoding.OscEncoder() + encoding.OscDebug()
                if "tuio" in uri.scheme: node += encoding.TuioDecoder()
            else:
                raise ValueError("Unexpected encoding: %s"%uri)
            # FIXME: start should be triggered at outputs ready
            QtCore.QTimer.singleShot(300, player.start)
        elif mode=="out":            
            if scheme in ("json", "json.slip"):
                query = parseQuery(uri, "request")
                assertUriQuery(uri, query)
                encoder = encoding.JsonEncoder(wrap=True, **query)
                encoder += encoding.TextEncoder()
            elif uri.scheme in ("osc", "osc.slip"):
                assertUriQuery(uri, None)
                encoder = encoding.OscEncoder(wrap=True)
            else:
                raise ValueError("Unknown log encoding: %s"%uri)
            device = create("slip.file://%s"%uri.path, "out", logger)
            node = encoder + device
        
        '''elif uri.scheme=="rec":
        if mode in ("", "out"):
            kwargs.update(parseQuery(uri, "timelimit", "sizelimit", 
                                      "oversizecut", "fps", "timewarping",
                                      "request", "hz"))
            kwargs.setdefault("request", "*")
            node = logger.Recorder(**kwargs)
            node.gui.show()
            node.gui.raise_()
        else:
            raise ValueError("Requested node is not an input: %s"%uri)'''

    # -------------------------------------------------------------------
    # IO DEVICES
    elif uri.scheme=="stdin":
        assertUriModeIn(uri, mode, "", "in")
        assertUriQuery(uri, None)
        if uri.opaque or uri.path or uri.site or uri.fragment: 
            raise ValueError("Invalid URI: %s"%uri)
        else:
            encoder = encoding.TextEncoder(blender=Functor.MERGE)
            reader = ioport.DataReader(CommunicationDevice(sys.stdin))
            node = reader + encoder

    elif uri.scheme=="stdout":
        assertUriModeIn(uri, mode, "", "out")
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
            if os.path.isfile(str(uri.path)):
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
    elif uri.scheme.startswith("slip."):
        assertUriModeIn(uri, mode, "in", "out")
        loweruri = lower(uri, "slip")
        if mode=="in":
            if "file" in loweruri.scheme: loweruri.query.data["uncompress"] = ""
            device = create(loweruri, "in", logger)
            decoder = encoding.SlipDecoder() # blender is fixed to  RESULTONLY
            textdecoder = encoding.TextDecoder(blender=Functor.MERGE)
            node = device + decoder + textdecoder
        elif mode=="out":
            encoder = encoding.SlipEncoder(blender=Functor.MERGE)
            textdecoder = encoding.TextDecoder(blender=Functor.MERGE)
            device = create(loweruri, "out", logger)
            node = encoder + textdecoder + device

    # JSON
    elif uri.scheme=="json":
        extended = copy.copy(uri)
        extended.scheme += ".slip.file" if uri.path else ".udp"
        logger.info(
            "No transport protocol specified in URI, assuming: %s"%extended.scheme)
        return create(extended, mode, logger, parent)

    elif uri.scheme.startswith("json."):
        assertUriModeIn(uri, mode, "in", "out")
        query = parseQuery(uri, "request", "noslip")
        loweruri = lower(uri, "json", query.keys())
        noslip = assertIsInstance(query.pop("noslip", False), bool)
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
            device = create(loweruri, "in", logger)
            decoder = encoding.JsonDecoder(blender=Functor.MERGE)
            node = device + decoder
        elif mode=="out":
            encoder = encoding.JsonEncoder(blender=Functor.RESULTONLY, **query)
            textencoder = encoding.TextEncoder(blender=Functor.MERGE)
            device = create(loweruri, "out", logger)
            node = encoder + textencoder + device

    # OSC
    elif uri.scheme=="osc":
        extended = copy.copy(uri)
        extended.scheme += ".slip.file" if uri.path else ".udp"
        logger.info(
            "No transport protocol specified in URI, assuming: %s"%extended.scheme)
        return create(extended, mode, logger, parent)

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
            device = create(loweruri, "in", logger)
            decoder = encoding.OscDecoder(blender=Functor.MERGE, **query)
            oscdebug = encoding.OscDebug(blender=Functor.MERGE)
            node = device + decoder + oscdebug

        elif mode=="out":
            encoder = encoding.OscEncoder(blender=Functor.RESULTONLY, **query)
            decoder = encoding.OscDecoder(blender=Functor.MERGE)
            oscdebug = encoding.OscDebug(blender=Functor.MERGE)
            device = create(loweruri, "out", logger)
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
        return create(extended, mode, logger, parent)

    elif uri.scheme.startswith("tuio."):
        assertUriModeIn(uri, mode, "in", "out")
        loweruri = lower(uri, "tuio")
        if not loweruri.scheme.startswith("osc."): 
            loweruri.scheme = "osc.%s"%loweruri.scheme
        if mode=="in":
            device = create(loweruri, "in", logger)
            encoder = encoding.TuioDecoder(blender=Functor.MERGE)
            node = device + encoder
        elif mode=="out":
            if loweruri.site.host and loweruri.site.port==0: 
                loweruri.site.port = 3333
            encoder = encoding.TuioEncoder(blender=Functor.RESULTONLY)
            device = create(loweruri, "out")
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
        return create(extended, mode, logger, parent)

    elif uri.scheme.startswith("dump."):
        from boing.nodes import Dump
        assertUriModeIn(uri, mode, "", "out")
        query = parseQuery(uri, "request", "src", "dest", "depth")
        dump = Dump(**query) # blender is fixed to  RESULTONLY
        encoder = encoding.TextEncoder(blender=Functor.MERGE)
        device = create(lower(uri, "dump", query.keys()), "out", logger)
        node = dump + encoder + device

    elif uri.scheme.startswith("stat."):
        from boing.nodes import StatProducer
        assertUriModeIn(uri, mode, "", "out")
        query = parseQuery(uri, "request", "filter", "hz", "fps")
        stat = StatProducer(**query) # blender is fixed to  RESULTONLY
        encoder = encoding.TextEncoder(blender=Functor.MERGE)
        device = create(lower(uri, "stat", query.keys()), "out", logger) 
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
        query = parseQuery(uri, "attr")
        assertUriQuery(uri, query)
        uri.opaque = Request(uri.opaque) if uri.opaque else Request.NONE
        if "attr" in query:
            uri.opaque += attrToRequest(query["attr"]) + Request("diff.removed")
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
            query["request"] = query.get("request", Request.NONE) + request
        elif "request" not in query:
            query["request"] = attrToRequest("rel_pos,rel_speed")
        query.setdefault("blender", Functor.MERGECOPY)
        node = Calibration(**query)

    # -------------------------------------------------------------------
    # LIB FILTERING PORT
    elif uri.scheme=="filtering":
        from boing.nodes import DiffArgumentFunctor
        import boing.extra.filtering as filtering
        query = parseQuery(uri, "attr", "request", "blender")
        filteruri = uri.query.data.get("uri", "fltr:/moving/mean?winsize=5")
        query["functorfactory"] = filtering.getFunctorFactory(filteruri)
        if "attr" in query:
            request = attrToRequest(query.pop("attr"))
            query["request"] = query.get("request", Request.NONE) + request
        elif "request" not in query:
            query["request"] = attrToRequest("rel_pos,rel_speed")
        node = DiffArgumentFunctor(**query)

    # -------------------------------------------------------------------
    # GRAPHERS
    elif uri.scheme.startswith("grapher."):
        assertUriModeIn(uri, mode, "", "out")
        if ".pydot" in uri.scheme:
            from boing.extra.pydot import DotGrapherProducer
            query = parseQuery(uri, "hz", "request", "maxdepth")
            assertUriQuery(uri, query)
            grapher = DotGrapherProducer(**query)
            #encoder = encoding.TextEncoder(blender=Functor.MERGE)
            #device = create(lower(uri, "grapher", query), mode="out")
            node = grapher #+ encoder + device
            node.grapher = grapher
        else:
            from boing.nodes import SimpleGrapherProducer
            query = parseQuery(uri, "hz", "request", "maxdepth")
            assertUriQuery(uri, query)
            grapher = SimpleGrapherProducer(**query)
            encoder = encoding.TextEncoder(blender=Functor.MERGE)
            device = create(lower(uri, "grapher", query), mode="out")
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
                rvalue[key] = Request(value)
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
    if schemecut: rvalue.scheme = rvalue.scheme.replace("%s."%schemecut, "", 1)
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
