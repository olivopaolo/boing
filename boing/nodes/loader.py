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

from PyQt4 import QtCore, QtGui

import boing.nodes.debug as debug
import boing.nodes.encoding as encoding
import boing.nodes.logger as logger
import boing.nodes.functions as functions
import boing.net.tcp as tcp
import boing.net.udp as udp
import boing.utils.fileutils as fileutils 
import boing.utils as utils

from boing.core.MappingEconomy import Tunnel, FilterOut, FunctionalNode
from boing.nodes.ioport import DataReader, DataWriter
from boing.nodes.multitouch.ContactViz import ContactViz
from boing.utils.url import URL


def create(uri, mode="", logger=None, **kwargs):
    """Return the node created from "uri"."""
    if mode not in ("", "in", "out"): raise ValueError("Invalid mode: %s"%mode)
    logger = logger if logger is not None else logging.getLogger("loader")
    uri = URL(str(uri))
    if not uri.opaque and not uri.scheme and not uri.path: 
        raise ValueError("Empty URI")
    kwargs = utils.quickdict(kwargs)

    # -------------------------------------------------------------------
    # IN: AND  OUT: REPLACED USING MODE
    if uri.scheme=="in":
        if mode not in ("", "in"): raise ValueError(
            "Invalid mode for %s: %s"%(uri, mode))
        else:
            return create(str(uri).replace("in:", "", 1), "in", **kwargs)

    elif uri.scheme=="out":
        if mode not in ("", "out"): raise ValueError(
            "Invalid mode for %s: %s"%(uri, mode))
        else:
            return create(str(uri).replace("out:", "", 1), "out", **kwargs)

    # -------------------------------------------------------------------
    # DATA REDIRECTION
    elif uri.scheme=="bridge":
        extended = copy.copy(uri)
        extended.scheme = "json.udp"
        if uri.site.port==0: extended.site.port = 7898
        if not uri.site.host and mode=="out": extended.site.host = "::1"
        return create(extended, mode, **kwargs)

    elif uri.scheme=="play":
        extended = copy.copy(uri)
        extended.scheme = "play.json"
        return create(extended, mode, **kwargs)

    elif uri.scheme.startswith("play."):
        if mode not in ("", "in"): raise ValueError(
            "Invalid mode for %s: %s"%(uri, mode))
        elif uri.kind==URL.OPAQUE or uri.site or uri.fragment: raise ValueError(
            "Invalid URI: %s"%uri)
        elif not uri.path: raise ValueError(
            "URI's path cannot be empty: %s"%uri)
        else:
            query = _uriquery(uri, "loop", "speed", "interval", "noslip")
            unexpected = list(filter(lambda k: not _isPost(k),
                                     uri.query.data.keys()-query.keys()))
            if unexpected: raise ValueError(
                "Unexpected query keys: %s"%", ".join(unexpected))
            elif uri.scheme in ("play.json", "play.json.slip"):
                kwargs.update(query)
                node = encoding.JsonLogPlayer(uri.path, **kwargs)
                node.addPost(encoding.TextEncoder())
            elif uri.scheme in ("play.osc", "play.osc.slip",
                                "play.tuio", "play.tuio.osc", "play.tuio.osc.slip"):
                kwargs.update(query)
                node = encoding.OscLogPlayer(uri.path, **kwargs)
                node.addPost(encoding.OscEncoder())
                node.addPost(encoding.OscDebug())
                if "tuio" in uri.scheme: node.addPost(encoding.TuioDecoder())
            else:
                raise ValueError("Unexpected encoding: %s"%uri)
            # FIXME: start should be triggered at outputs ready
            QtCore.QTimer.singleShot(300, node.start)
        
    elif uri.scheme=="log":
        return create(str(uri).replace("log:", "log.json:", 1), mode, **kwargs)

    elif uri.scheme.startswith("log."):
        if mode in ("", "out"):
            if uri.kind==URL.OPAQUE or uri.site or uri.fragment: 
                raise ValueError("Invalid URI: %s"%uri)
            elif uri.scheme in ("log.json", "log.json.slip"):
                query = _uriquery(uri, "request", "filter")
                unexpected = list(filter(lambda k: not _isPre(k),
                                         uri.query.data.keys()-query.keys()))
                if unexpected: raise ValueError(
                    "Unexpected query keys: %s"%", ".join(unexpected))
                _filter = query.pop("filter", None)
                node = encoding.JsonEncoder(**dict(query, **kwargs))
                node.addPost(encoding.TextEncoder())
                # FIXME: filter not uniformly implemented
                if _filter is not None: 
                    node.setRequest(uri.query.data["filter"])
                    node.addPre(functions.Filter(uri.query.data["filter"]))
            elif uri.scheme in ("log.osc", "log.osc.slip"):
                unexpected = list(filter(lambda k: not _isPre(k),
                                         uri.query.data))
                if unexpected: raise ValueError(
                    "Unexpected query keys: %s"%", ".join(unexpected))
                else:
                    node = encoding.OscEncoder(wrap=True, **kwargs)
            else:
                raise ValueError("Unknown log encoding: %s"%uri)
            node.addObserver(
                create("slip.file://%s"%uri.path, "out", parent=node))
        else:
            raise ValueError("Requested node is not an input: %s"%uri)
        
        '''elif uri.scheme=="rec":
        if mode in ("", "out"):
            kwargs.update(_uriquery(uri, "timelimit", "sizelimit", 
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
        if mode not in ("", "in"): raise ValueError(
            "Invalid mode for %s: %s"%(uri, mode))
        elif mode in ("", "in"):
            if uri.opaque or uri.path or uri.site or uri.fragment: 
                raise ValueError("Invalid URI: %s"%uri)
            else:
                unexpected = list(filter(lambda k: not _isPost(k),
                                         uri.query.data))
                if unexpected: raise ValueError(
                    "Unexpected query keys: %s"%", ".join(unexpected))
                node = DataReader(fileutils.CommunicationDevice(sys.stdin), 
                                  **kwargs)
                node.addPost(encoding.TextEncoder())

    elif uri.scheme=="stdout":
        if mode not in ("", "out"): raise ValueError(
            "Invalid mode for %s: %s"%(uri, mode))
        elif mode in ("", "out"):
            if uri.opaque or uri.path or uri.site or uri.fragment: 
                raise ValueError("Invalid URI: %s"%uri)
            else:
                unexpected = list(filter(lambda k: not _isPre(k),
                                         uri.query.data))
                if unexpected: raise ValueError(
                    "Unexpected query keys: %s"%", ".join(unexpected))
                node = DataWriter(fileutils.IODevice(sys.stdout), **kwargs)

    elif uri.scheme in ("", "file"):
        if uri.kind==URL.OPAQUE or uri.site or uri.fragment: 
            raise ValueError("Invalid URI: %s"%uri)
        elif not uri.path: 
            raise ValueError("URI's path cannot be empty: %s"%uri)
        elif mode not in ("in", "out"): raise ValueError(
            "Invalid mode for %s: %s"%(uri, mode))
        elif mode=="in":
            query = _uriquery(uri, "uncompress", "postend")
            unexpected = list(filter(lambda k: not _isPost(k),
                                     uri.query.data.keys()-query.keys()))
            if unexpected: raise ValueError(
                "Unexpected query keys: %s"%", ".join(unexpected))
            if "postend" in query: kwargs.postend = query.pop("postend")
            filepath = str(uri.path)
            if os.path.isfile(filepath):
                inputfile = fileutils.FileReader(uri, **query)
                # FIXME: start should be triggered at outputs ready
                QtCore.QTimer.singleShot(300, inputfile.start)
            else:
                inputfile = fileutils.CommunicationFile(uri)
            node = DataReader(inputfile, **kwargs)
            node.addPost(encoding.TextEncoder() \
                             if inputfile.isTextModeEnabled() \
                             else encoding.TextDecoder())
        elif mode=="out":
            unexpected = list(filter(lambda k: not _isPre(k),
                                     uri.query.data))
            if unexpected: raise ValueError(
                "Unexpected query keys: %s"%", ".join(unexpected))
            node = DataWriter(fileutils.File(uri, fileutils.File.WriteOnly), 
                              **kwargs)

    elif uri.scheme=="udp":
        if uri.kind==URL.OPAQUE or uri.path or uri.fragment: 
            raise ValueError("Invalid URI: %s"%uri)
        elif mode not in ("in", "out"): raise ValueError(
            "Invalid mode for %s: %s"%(uri, mode))
        elif mode=="in":
            unexpected = list(filter(lambda k: not _isPost(k), uri.query.data))
            if unexpected: raise ValueError(
                "Unexpected query keys: %s"%", ".join(unexpected))
            node = DataReader(udp.UdpListener(uri), **kwargs)
            node.addPost(encoding.TextDecoder())
            if uri.site.port==0: logger.info(
                "Listening at %s"%node.inputDevice().url())
        elif mode=="out":
            query = _uriquery(uri, "writeend")
            unexpected = list(filter(lambda k: not _isPre(k),
                                     uri.query.data.keys()-query.keys()))
            if unexpected: raise ValueError(
                "Unexpected query keys: %s"%", ".join(unexpected))
            node = DataWriter(udp.UdpSender(uri), **dict(query, **kwargs))

    elif uri.scheme=="tcp":
        if uri.kind==URL.OPAQUE or uri.path or uri.fragment: 
            raise ValueError("Invalid URI: %s"%uri)
        elif mode not in ("in", "out"): raise ValueError(
            "Invalid mode for %s: %s"%(uri, mode))
        elif mode=="in":
            unexpected = list(filter(lambda k: not _isPost(k), uri.query.data))
            if unexpected: raise ValueError(
                "Unexpected query keys: %s"%", ".join(unexpected))
            node = Tunnel(request="data", **kwargs)
            node.addPost(encoding.TextDecoder())
            server = NodeServer(uri.site.host, uri.site.port, parent=node)
            if uri.site.port==0: logger.info(
                "Listening at %s"%server.url())
        elif mode=="out":
            unexpected = list(filter(lambda k: not _isPre(k), uri.query.data))
            if unexpected: raise ValueError(
                "Unexpected query keys: %s"%", ".join(unexpected))
            node = DataWriter(tcp.TcpConnection(uri), **kwargs)

    # -------------------------------------------------------------------
    # ENCODINGS
    # SLIP
    elif uri.scheme.startswith("slip."):
        if mode not in ("in", "out"): raise ValueError(
            "Invalid mode for %s: %s"%(uri, mode))
        elif mode=="in":
            unexpected = list(filter(lambda k: _isPre(k), uri.query.data))
            if unexpected: raise ValueError(
                "Unexpected query keys: %s"%", ".join(unexpected))
            lower = LowerURI(uri, "slip")
            if "file" in lower.scheme: lower.query.data["uncompress"] = ""
            node = create(lower, "in", **kwargs)
            node.addPost(
                encoding.SlipDecoder().addPost(
                    encoding.TextDecoder()))
        elif mode=="out":
            unexpected = list(filter(lambda k: _isPost(k), uri.query.data))
            if unexpected: raise ValueError(
                "Unexpected query keys: %s"%", ".join(unexpected))
            lower = LowerURI(uri, "slip")
            node = create(lower, "out", **kwargs)
            node.addPre(encoding.SlipEncoder().addPost(encoding.TextDecoder()))

    # JSON
    elif uri.scheme=="json":
        extended = copy.copy(uri)
        extended.scheme += ".slip.file" if uri.path else ".udp"
        logger.info(
            "No transport protocol specified in URI, assuming: %s"%extended.scheme)
        return create(extended, mode, **kwargs)

    elif uri.scheme.startswith("json."):
        if mode not in ("in", "out"): raise ValueError(
            "Invalid mode for %s: %s"%(uri, mode))
        else:
            query = _uriquery(uri, "request", "filter", "noslip")
            lower = LowerURI(uri, "json", *query.keys())
            noslip = query.pop("noslip", False)
            if not isinstance(noslip, bool): raise TypeError(
                "noslip must be boolean, not '%s'"%noslip.__class__.__name__)
            elif not noslip:
                if lower.scheme=="file":
                    lower.scheme = "slip.%s"%lower.scheme
                    logger.info(
                        "JSON over FILE is SLIP encoded by default (set noslip to disable)")
                if lower.scheme=="tcp":
                    lower.scheme = "slip.%s"%lower.scheme
                    logger.info(
                        "JSON over TCP is SLIP encoded by default (set noslip to disable)")
            if mode=="in":
                if "request" in query: raise ValueError(
                    "Unexpected query key: request")
                if "filter" in query: raise ValueError(
                    "Unexpected query key: filter")
                unexpected = list(filter(lambda k: _isPre(k), uri.query.data))
                if unexpected: raise ValueError(
                    "Unexpected query keys: %s"%", ".join(unexpected))
                node = encoding.JsonDecoder(**dict(query, **kwargs))
                node.subscribeTo(create(lower, "in", parent=node))
            elif mode=="out":
                unexpected = list(filter(lambda k: _isPost(k), uri.query.data))
                if unexpected: raise ValueError(
                    "Unexpected query keys: %s"%", ".join(unexpected))
                if "filter" not in query: _filter = None
                else:
                    _filter = functions.Filter(query.pop("filter"))
                    query.setdefault("request", _filter.query())
                node = encoding.JsonEncoder(**dict(query, **kwargs))
                node.addPost(encoding.TextEncoder())
                if _filter is not None: node.addPre(_filter)
                node.addObserver(create(lower, "out", parent=node))

    # OSC
    elif uri.scheme=="osc":
        extended = copy.copy(uri)
        extended.scheme += ".slip.file" if uri.path else ".udp"
        logger.info(
            "No transport protocol specified in URI, assuming: %s"%extended.scheme)
        return create(extended, mode, **kwargs)

    elif uri.scheme.startswith("osc."):
        if mode not in ("in", "out"): raise ValueError(
            "Invalid mode for %s: %s"%(uri, mode))
        else:
            query = _uriquery(uri, "rt", "noslip")
            lower = LowerURI(uri, "osc", *query.keys())
            noslip = query.pop("noslip", False)
            if not isinstance(noslip, bool): raise TypeError(
                "noslip must be boolean, not '%s'"%noslip.__class__.__name__)
            elif not noslip:
                if lower.scheme=="file":
                    lower.scheme = "slip.%s"%lower.scheme
                    logger.info(
                        "OSC over FILE is SLIP encoded by default (set noslip to disable)")
                if lower.scheme=="tcp":
                    lower.scheme = "slip.%s"%lower.scheme
                    logger.info(
                        "OSC over TCP is SLIP encoded by default (set noslip to disable)")
            if mode=="in":
                unexpected = list(filter(lambda k: _isPre(k), uri.query.data))
                if unexpected: raise ValueError(
                    "Unexpected query keys: %s"%", ".join(unexpected))
                node = create(lower, "in", **kwargs)
                node.addPost(FilterOut("str"))
                node.addPost(
                    encoding.OscDecoder(**query).addPost(encoding.OscDebug()))
            elif mode=="out":
                unexpected = list(filter(lambda k: _isPost(k), uri.query.data))
                if unexpected: raise ValueError(
                    "Unexpected query keys: %s"%", ".join(unexpected))
                node = encoding.OscEncoder(resultmode=FunctionalNode.RESULTONLY, 
                                           **dict(query, **kwargs))
                node.addPost(encoding.OscDecoder())
                node.addPost(encoding.OscDebug())
                node.addObserver(create(lower, "out", parent=node))

    # TUIO
    elif uri.scheme=="tuio":
        extended = copy.copy(uri)
        if uri.path: extended.scheme += ".osc.slip.file"
        else:            
            extended.scheme += ".osc.udp"
            if uri.site.port==0: extended.site.port = 3333
        logger.info(
            "No transport protocol specified in URI, assuming: %s"%extended.scheme)
        return create(extended, mode, **kwargs)

    elif uri.scheme.startswith("tuio."):
        lower = LowerURI(uri, "tuio")
        if not lower.scheme.startswith("osc."): 
            lower.scheme = "osc.%s"%lower.scheme
        if mode=="in":
            unexpected = list(filter(lambda k: _isPre(k), uri.query.data))
            if unexpected: raise ValueError(
                "Unexpected query keys: %s"%", ".join(unexpected))
            node = create(lower, "in", **kwargs)
            node.addPost(encoding.TuioDecoder())
        elif mode=="out":
            unexpected = list(filter(lambda k: _isPost(k), uri.query.data))
            if unexpected: raise ValueError(
                "Unexpected query keys: %s"%", ".join(unexpected))
            node = encoding.TuioEncoder(**kwargs)
            if lower.site.host and lower.site.port==0: lower.site.port = 3333
            node.addObserver(create(lower, "out", parent=node))
        elif not mode:
            raise NotImplementedError()            

    # MT-DEV
    elif uri.scheme=="mtdev":
        if sys.platform == "linux2":
            if mode not in ("", "in"): raise ValueError(
                "Invalid mode for %s: %s"%(uri, mode))
            elif mode in ("", "in"):
                import boing.extra.mtdev
                node = boing.extra.mtdev.MtDevDevice(str(uri.path), **kwargs)
        else:
            raise ImportError(
                "'libmtdev' is not available on this platform: %s"%sys.platform)

    # -------------------------------------------------------------------
    # DATA PROCESSING
    elif uri.scheme=="nop":
        unexpected = list(filter(lambda k: not _isPost(k) or not _isPre(k), 
                                 uri.query.data))
        if unexpected: raise ValueError(
            "Unexpected query keys: %s"%", ".join(unexpected))
        node = Tunnel(**kwargs)

    elif uri.scheme in ("dump", "stat"):
        extended = copy.copy(uri)
        extended.scheme += ".udp" if extended.site \
            else ".file" if extended.path \
            else ".stdout"
        return create(extended, mode, **kwargs)

    elif uri.scheme.startswith("dump."):
        if mode not in ("", "out"): raise ValueError(
            "Invalid mode for %s: %s"%(uri, mode))
        elif mode in ("", "out"):
            query = _uriquery(uri, "request", "filter", "src", "dest", "depth")
            unexpected = list(filter(lambda k: _isPost(k), uri.query.data))
            if unexpected: raise ValueError(
                "Unexpected query keys: %s"%", ".join(unexpected))
            if "filter" not in query: _filter = None
            else:
                _filter = functions.Filter(query.pop("filter"))
                query.setdefault("request", _filter.query())
            node = debug.DumpNode(**dict(query, **kwargs))
            node.addPost(encoding.TextEncoder())
            if _filter is not None: node.addPre(_filter)
            lower = LowerURI(uri, "dump", "filter", *query.keys())
            node.addObserver(create(lower, "out", parent=node))

    elif uri.scheme.startswith("stat."):
        if mode not in ("", "out"): raise ValueError(
            "Invalid mode for %s: %s"%(uri, mode))
        elif mode in ("", "out"):
            query = _uriquery(uri, "request", "filter", "hz")
            unexpected = list(filter(lambda k: _isPost(k), uri.query.data))
            if unexpected: raise ValueError(
                "Unexpected query keys: %s"%", ".join(unexpected))
            if "filter" not in query: _filter = None
            else:
                _filter = functions.Filter(query.pop("filter"))
                query.setdefault("request", _filter.query())
            node = debug.StatProducer(**dict(query, **kwargs))
            node.addPost(encoding.TextEncoder())
            if _filter is not None: node.addPre(_filter)
            lower = LowerURI(uri, "stat", "filter", *query.keys())
            node.addObserver(create(lower, "out", parent=node))

    elif uri.scheme=="viz":
        if mode not in ("", "out"): raise ValueError(
            "Invalid mode for %s: %s"%(uri, mode))
        elif mode in ("", "out"):
            if uri.opaque or uri.path or uri.site or uri.fragment: 
                raise ValueError("Invalid URI: %s"%uri)
            else:
                query  = _uriquery(uri, "antialiasing", "fps")
                unexpected = list(filter(lambda k: not _isPre(k),
                                         uri.query.data.keys()-query.keys()))
                if unexpected: raise ValueError(
                    "Unexpected query keys: %s"%", ".join(unexpected))
                node = ContactViz(**dict(query, **kwargs))

    elif uri.scheme=="filter" and uri.kind==URL.OPAQUE:
        kwargs.update(_uriquery(uri, "request", "hz"))
        node = functions.Filter(uri.opaque, **kwargs)

    elif uri.scheme=="filterout":
        kwargs.update(_uriquery(uri, "hz"))
        request = uri.opaque if uri.opaque else "*"
        node = FilterOut(request, **kwargs)

    elif uri.scheme=="lag":
        kwargs.update(_uriquery(uri, "request"))
        msec = int(uri.opaque) if uri.opaque else 200
        node = functions.Lag(msec, **kwargs)

    elif uri.scheme=="timekeeper":
        node = functions.Timekeeper(**kwargs)

    elif uri.scheme=="calib":
        matrix = None
        args = _uriquery(uri, "matrix", "screen")
        if "matrix" in args: 
            values = tuple(map(float, args.matrix.strip().split(",")))
            kwargs.matrix = QtGui.QMatrix4x4(*values)
        elif "screen" in args:
            if args.screen=="normal": 
                kwargs.matrix = functions.Calibration.Identity
            elif args.screen=="left": 
                kwargs.matrix = functions.Calibration.Left
            elif args.screen=="inverted": 
                kwargs.matrix = functions.Calibration.Inverted
            elif args.screen=="right": 
                kwargs.matrix = functions.Calibration.Right
        else: kwargs.matrix = functions.Calibration.Identity
        kwargs.update(_uriquery(uri, "args", "request", "resultmode"))
        if "args" not in kwargs:
            kwargs.template = utils.quickdict()
            kwargs.args = ""
            default = "rel_pos|rel_speed|boundingbox.rel_pos"
            for attr in uri.query.data.get("attr", default).split("|"):
                if kwargs.args: kwargs.args += "|"
                kwargs.args += "diff.added,updated.contacts.*." + attr
                # Add attribute to template
                for action in ("added", "updated"):                    
                    item = kwargs.template.diff[action].contacts["*"]
                    for key in attr.split("."):
                        if not key: break
                        else:
                            item = item[key]
        node = functions.Calibration(**kwargs)

    # -------------------------------------------------------------------
    # LIB FILTERING PORT
    elif uri.scheme=="filtering":
        import boing.extra.filtering as filtering
        kwargs.update(_uriquery(uri, "args", "request", "resultmode"))
        kwargs.setdefault("resultmode", FunctionalNode.MERGECOPY)
        uri = uri.query.data.get("uri", "fltr:/moving/mean?winsize=5")
        kwargs.functorfactory = filtering.getFunctorFactory(uri)
        if "args" in kwargs:
            node = functions.ArgumentFunctor(**kwargs)
        else:
            # Using contact diff as default
            kwargs.template = utils.quickdict()
            kwargs.args = "diff.removed.contacts"       
            for attr in uri.query.data.get("attr", "rel_pos").split("|"):
                kwargs.args += "|diff.added,updated.contacts.*." + attr
                # Add attribute to template
                for action in ("added", "updated"):                    
                    item = kwargs.template.diff[action].contacts["*"]
                    for key in attr.split("."):
                        if not key: break
                        else:
                            item = item[key]
            node = functions.DiffArgumentFunctor(**kwargs)

    else:
        raise ValueError("Invalid URI: %s"%uri)

    # -------------------------------------------------------------------
    # POST & PRE ARGS
    for key, value in _uriquery(uri).items():
        # Post
        if _isPost(key):
            posturi = URL(value)
            post = create(posturi)
            if isinstance(post, FunctionalNode) and "resultmode" not in posturi:
                post._resultmode = FunctionalNode.MERGE
            node.addPost(post)
        # Pre
        if _isPre(key):
            preuri = URL(value)
            pre = create(preuri)
            if isinstance(pre, FunctionalNode) and "resultmode" not in preuri:
                pre._resultmode = FunctionalNode.MERGECOPY
            node.addPre(pre)
    return node

# -------------------------------------------------------------------

class NodeServer(tcp.TcpServer):
    def __init__(self, *args, **kwargs):
        tcp.TcpServer.__init__(self, *args, **kwargs)
        self.newConnection.connect(self.__newConnection)
    def __newConnection(self): 
        conn = self.nextPendingConnection()
        reader = DataReader(conn, parent=conn)
        reader.addObserver(self.parent())

def _uriquery(uri, *restrictions):
    """Return a dict obtained from the uri query data filtered using
    the key list restrictions. If restrictions is empty all the query
    data is preserved. The query data values are converted using the
    function '_kwstr2value'."""
    rvalue = utils.quickdict()
    for key, value in uri.query.data.items():
        if not restrictions or key in restrictions:
            if key=="resultmode":
                if value.lower()=="merge":
                    rvalue[key] = FunctionalNode.MERGE
                elif value.lower()=="copy":
                    rvalue[key] = FunctionalNode.MERGECOPY
                elif value.lower()=="result":
                    rvalue[key] = FunctionalNode.RESULTONLY
                else:
                    raise ValueError("Unexpected mode value: %s"%value)
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

def _isPost(key):
    """Return True if 'key' matches "postN", where N can be an
    integer or nothing (e.g. post, post1, post2, etc.)."""
    first, partition, end = key.partition("post")
    return first=="" and partition=="post" and (end=="" or end.isdecimal())

def _isPre(key):
    """Return True if 'key' matches "preN", where N can be an
    integer or nothing (e.g. pre, pre1, pre2, etc.)."""
    first, partition, end = key.partition("pre")
    return first=="" and partition=="pre" and (end=="" or end.isdecimal())

def LowerURI(uri, schemecut="", *additional):
    """Return a copy of 'uri' where:
        - 'schemecut' is removed from the uri's scheme;
        - all keys in 'additional' are removed from the uri's query data;
        - all post* and pre* key-values are removed from the uri's query data;
    """
    rvalue = URL(str(uri))
    if schemecut: rvalue.scheme = rvalue.scheme.replace("%s."%schemecut, "", 1)
    f = lambda k: not (_isPost(k) or _isPre(k) or k in additional)
    rvalue.query.data = dict((k,v) for k,v in rvalue.query.data.items() if f(k))
    return rvalue
