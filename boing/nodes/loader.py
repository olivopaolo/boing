# -*- coding: utf-8 -*-
#
# boing/nodes/loader.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import os
import sys

from PyQt4 import QtCore, QtGui

import boing.nodes.debug as debug
import boing.nodes.encoding as encoding
import boing.nodes.functions as functions
import boing.net.tcp as tcp
import boing.net.udp as udp
import boing.utils.fileutils as fileutils 
import boing.utils as utils

from boing.core.MappingEconomy import \
    Node, TunnelNode, FilterOut, FunctionalNode
from boing.nodes.ioport import DataReader, DataWriter
from boing.nodes.multitouch.ContactViz import ContactViz
from boing.utils.url import URL

try:    
    import boing.extra.filtering as filtering
except ImportError:
    print("WARNING! Module filtering is not available.")

if sys.platform=='linux2':
    try:    
        import boing.extra.mtdev as mtdev
    except ImportError:
        print("WARNING! Module mtdev is not available.")


def create(url, mode="", **kwargs):
    """Create a new node from the argument "url"."""
    if mode not in ("", "in", "out"): raise ValueError("Invalid mode: %s"%mode)
    url = URL(str(url))
    kwargs = utils.quickdict(kwargs)

    # -------------------------------------------------------------------
    # IN. AND  OUT. REPLACED USING MODE
    if url.scheme.startswith("in."):
        if mode in ("", "in"):
            url = str(url).replace("in.", "", 1)
            return create(url, "in", **kwargs)
        else:
            raise Exception("Requested node is not an output: %s"%str(url))

    elif url.scheme.startswith("out."):
        if mode in ("", "out"):
            url = str(url).replace("out.", "", 1)
            return create(url, "out", **kwargs)
        else:
            raise Exception("Requested node is not an input: %s"%str(url))

    # -------------------------------------------------------------------
    # UTILS
    elif url.scheme=="dump":
        url.scheme += ".stdout"
        return create(url, mode, **kwargs)

    elif url.scheme.startswith("dump."):
        if mode in ("", "out"):
            lower = LowerURL(str(url).replace("dump.", "", 1))
            node = create(lower, "out", **kwargs)
            args = _filterargs(url, "src", "dest", "depth", "request", "hz")
            node.addPre(debug.DumpNode(**args).addPost(encoding.TextEncoder()))
            node.addPre(FilterOut("str|data"))
        else:
            raise Exception("Requested node is not an input: %s"%str(url))

    elif url.scheme=="stat":
        url.scheme += ".stdout"
        return create(url, mode, **kwargs)

    elif url.scheme.startswith("stat."):
        if mode in ("", "out"):
            lower = LowerURL(str(url).replace("stat.", "", 1))
            node = create(lower, "out", **kwargs)
            args = _filterargs(url, "request", "hz")
            node.addPre(debug.StatProducer(**args).addPost(encoding.TextEncoder()))
            node.addPre(FilterOut("str|data"))
        else:
            raise Exception("Requested node is not an input: %s"%str(url))

    # -------------------------------------------------------------------
    # BRIDGES
    elif url.scheme=="stdin":
        if mode in ("", "in"):
            node = DataReader(fileutils.CommunicationDevice(sys.stdin), **kwargs)
            node.addPost(encoding.TextEncoder())
        else:
            raise Exception("Requested node is not an output: %s"%str(url))        

    elif url.scheme=="stdout":
        if mode in ("", "out"):
            node = DataWriter(fileutils.IODevice(sys.stdout), **kwargs)
        else:
            raise Exception("Requested node is not an input: %s"%str(url))

    elif url.scheme in ("", "file"):
        if mode=="in":
            filepath = str(url.path)
            if os.path.isfile(filepath):
                inputfile = fileutils.FileReader(
                    url, **_filterargs(url, "uncompress"))
                # FIXME: start should be triggered at outputs ready
                QtCore.QTimer.singleShot(300, inputfile.start)
            else:
                inputfile = fileutils.CommunicationFile(url)
            kwargs.update(_filterargs(url, "postend"))
            node = DataReader(inputfile, **kwargs)
            node.addPost(encoding.TextEncoder() \
                             if inputfile.isTextModeEnabled() \
                             else encoding.TextDecoder())
        elif mode=="out":
            node = DataWriter(
                fileutils.File(url, fileutils.File.WriteOnly), **kwargs)
        elif not mode:
            raise NotImplementedError()

    elif url.scheme=="udp":
        if mode=="in":
            node = DataReader(udp.UdpListener(url), **kwargs)
            node.addPost(encoding.TextDecoder())
        elif mode=="out":
            kwargs.update(_filterargs(url, "writeend"))
            node = DataWriter(udp.UdpSender(url), **kwargs)
        elif not mode:
            raise NotImplementedError()

    elif url.scheme=="tcp":
        if mode=="in":
            node = TunnelNode(request="data", **kwargs)
            node.addPost(encoding.TextDecoder())
            server = NodeServer(url.site.host, url.site.port, parent=node)
        elif mode=="out":
            node = DataWriter(tcp.TcpConnection(url), **kwargs)
        elif not mode:
            raise NotImplementedError()

    # -------------------------------------------------------------------
    # SLIP ENCODING
    elif url.scheme.startswith("slip."):
        if mode=="in":
            lower = LowerURL(str(url).replace("slip.", "", 1))
            lower.query.data["uncompress"] = ""
            node = create(lower, "in", **kwargs)
            node.addPost(
                encoding.SlipDecoder().addPost(
                    encoding.TextDecoder()))
        elif mode=="out":
            lower = LowerURL(str(url).replace("slip.", "", 1))
            node = create(lower, "out", **kwargs)
            node.addPre(encoding.SlipEncoder().addPost(encoding.TextDecoder()))
        elif not mode:
            raise NotImplementedError()

    # -------------------------------------------------------------------
    # OSC ENCODING
    elif url.scheme=="osc":
        url = URL(str(url))
        if not str(url.path): url.scheme += ".udp"
        else: 
            url.scheme += ".log"
            url.query.data["uncompress"] = ""
        print("No transport protocol specified in URL, assuming: %s"%url.scheme)
        return create(url, mode, **kwargs)

    elif url.scheme=="osc.log":
        if mode=="in":
            kwargs.update(_filterargs(url, "loop", "speed"))
            node = encoding.OscLogPlayer(fileutils.File(url, uncompress=True), 
                                         **kwargs)
            node.addPost(encoding.OscEncoder())
            node.addPost(encoding.OscDebug())
            # FIXME: start should be triggered at outputs ready
            QtCore.QTimer.singleShot(300, node.start)
        elif mode=="out":
            kwargs.update(_filterargs(url, "raw"))
            node = encoding.OscLogFile(fileutils.File(url, fileutils.File.WriteOnly), 
                                       **kwargs)
            print("Ctrl-C to stop and close file.")
        elif not mode:
            raise NotImplementedError()

    elif url.scheme.startswith("osc."):
        if mode=="in":
            lower = LowerURL(str(url).replace("osc.", "", 1))
            node = create(lower, "in", **kwargs)
            node.addPost(FilterOut("str"))
            args = _filterargs(url, "rt")
            node.addPost(encoding.OscDecoder(**args).addPost(encoding.OscDebug()))
        elif mode=="out":
            lower = LowerURL(str(url).replace("osc.", "", 1))
            node = create(lower, "out", **kwargs)
            node.addPre(encoding.OscEncoder())
            node.addPre(encoding.OscDebug())
            node.addPre(FilterOut("str|data"))
        elif not mode:
            raise NotImplementedError()

    # -------------------------------------------------------------------
    # TUIO ENCODING
    elif url.scheme=="tuio":
        if str(url.path): 
            url.scheme += ".osc.log"
        elif mode=="in":
            url.scheme += ".osc.udp"
            if url.site.port==0: url.site.port = 3333
        elif mode=="out":
            if not url.site.host and url.site.port==0:
                url.scheme += ".stdout" 
            else:
                url.scheme += ".osc.udp"
                if not url.site.host: url.site.host="127.0.0.1"
                elif url.site.port==0: url.site.port=3333
        elif not mode:
            raise NotImplementedError()
        print("No transport protocol specified in URL, assuming: %s"%url.scheme)
        return create(url, mode, **kwargs)

    elif url.scheme.startswith("tuio."):
        if mode=="in":
            lower = LowerURL(str(url).replace("tuio.", "", 1) \
                if "osc." in url.scheme \
                else str(url).replace("tuio.", "osc.", 1))
            node = create(lower, "in", **kwargs)
            node.addPost(encoding.TuioDecoder())
        elif mode=="out":
            lower = LowerURL(str(url).replace("tuio.", "", 1) \
                if "osc." in url.scheme \
                else str(url).replace("tuio.", "osc.", 1))
            node = create(lower, "out", **kwargs)
            node.addPre(encoding.TuioEncoder())
            node.addPre(FilterOut("osc|data|str"))
        elif not mode:
            raise NotImplementedError()            

    # -------------------------------------------------------------------
    # MULTI-TOUCH INTERACTION
    elif url.scheme=="mtdev":
        if sys.platform == "linux2":
            if mode in ("", "in"):
                kwargs.update(_filterargs(url, "parent"))
                node = mtdev.MtDevDevice(str(url.path), **kwargs)
            else:
                raise Exception("Requested node is not an output: %s"%str(url))
        else:
            raise Exception(
                "'libmtdev' is not available on this platform: %s"%sys.platform)

    elif url.scheme=="viz":
        if mode in ("", "out"):
            kwargs.update(_filterargs(url, "antialiasing", "fps", "request"))
            node = ContactViz(**kwargs)
        else:
            raise Exception("Requested node is not an input: %s"%str(url))


    # -------------------------------------------------------------------
    # FUNCTIONS
    elif url.scheme=="filter" and url.kind==URL.OPAQUE:
        kwargs.update(_filterargs(url, "request", "hz"))
        node = functions.Filter(url.opaque, **kwargs)

    elif url.scheme=="filterout":
        kwargs.update(_filterargs(url, "hz"))
        request = url.opaque if url.opaque else "*"
        node = FilterOut(request, **kwargs)

    elif url.scheme=="lag":
        kwargs.update(_filterargs(url, "request"))
        msec = int(url.opaque) if url.opaque else 200
        node = functions.Lag(msec, **kwargs)

    elif url.scheme=="timekeeper":
        node = functions.Timekeeper(**kwargs)

    elif url.scheme=="calib":
        matrix = None
        args = _filterargs(url, "matrix", "screen")
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
        kwargs.update(_filterargs(url, "args", "request", "resultmode"))
        if "args" not in kwargs:
            kwargs.template = utils.quickdict()
            kwargs.args = ""
            default = "rel_pos|rel_speed|boundingbox.rel_pos"
            for attr in url.query.data.get("attr", default).split("|"):
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

    elif url.scheme=="filtering":
        kwargs.update(_filterargs(url, "args", "request", "resultmode"))
        kwargs.setdefault("resultmode", FunctionalNode.MERGECOPY)
        uri = url.query.data.get("uri", "fltr:/moving/mean?winsize=5")
        kwargs.functorfactory = filtering.getFunctorFactory(uri)
        if "args" in kwargs:
            node = functions.ArgumentFunctor(**kwargs)
        else:
            # Using contact diff as default
            kwargs.template = utils.quickdict()
            kwargs.args = "diff.removed.contacts"       
            for attr in url.query.data.get("attr", "rel_pos").split("|"):
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
        raise Exception("Invalid URL: %s"%url)

    # -------------------------------------------------------------------
    # POST & PRE ARGS
    kwargs = _filterargs(url)
    for key, value in kwargs.items():
        # Post
        first, partition, end = key.partition("post")
        if first=="" and partition=="post" and (end=="" or end.isdecimal()):
            posturl = URL(value)
            posturl.query.data.setdefault("resultmode", "merge")
            node.addPost(create(posturl))
        # Pre
        first, partition, end = key.partition("pre")
        if first=="" and partition=="pre" and (end=="" or end.isdecimal()):
            posturl = URL(value)
            posturl.query.data.setdefault("resultmode", "copy")
            node.addPre(create(value))

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


def _filterargs(url, *restrictions):
    rvalue = utils.quickdict()
    for key, value in url.query.data.items():
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
                rvalue[key] = _kwstr2value(url.query.data[key])
    return rvalue

def _kwstr2value(string):
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

def LowerURL(aString):
    """Returns an URL without the post and pre query arguments."""
    url = URL(str(aString))
    # Remove post query 
    for key in tuple(url.query.data.keys()):
        first, partition, end = key.partition("post")
        if first=="" and partition=="post" and (end=="" or end.isdecimal()):
            del url.query.data[key]
    # Remove pre query 
    for key in tuple(url.query.data.keys()):
        first, partition, end = key.partition("pre")
        if first=="" and partition=="pre" and (end=="" or end.isdecimal()):
            del url.query.data[key]
    return url

'''
def JSONReader(url):
    if not isinstance(url, URL): url = URL(str(url))
    decoder = JSONDecoder()
    if url.scheme in ("json", "json.udp"):
        endpoint = DataReader(udp.UdpListener(url), parent=decoder)
        decoder.subscribeTo(endpoint)
    elif url.scheme=="json.tcp":
        class ClientWaiter(QtCore.QObject):
            def __init__(self, parent):
                QtCore.QObject.__init__(self, parent)
                self.socket = None
            def newConnection(self): 
                server = self.sender()
                conn = server.nextPendingConnection()
                if not self.socket:
                    reader = encoding.SlipDataReader(conn, parent=decoder)
                    self.parent().subscribeTo(reader)
                    self.socket = conn
                    self.socket.disconnected.connect(self.disconnected)
                else:
                    conn.close()
            def disconnected(self):
                decoder = self.parent()
                for o in decoder.observed():
                    decoder.unsubscribeFrom(o)
                self.socket = None
        waiter = ClientWaiter(parent=decoder)
        server = tcp.TcpServer(url.site.host, url.site.port, parent=decoder)
        server.newConnection.connect(waiter.newConnection)
    else:
        decoder = None
        print("Unrecognized JSON url:", url)
    return decoder


def JSONWriter(url):
    if not isinstance(url, URL): url = URL(str(url))
    req = url.query.data.get('req')
    kwargs = {"requests": parseRequests(req)} if req is not None \
        else dict()
    encoder = JSONEncoder(**kwargs)
        # if url.kind in (URL.ABSPATH, URL.RELPATH) \
        #     or url.scheme=="tuio.file" \
        #     or (url.scheme=="tuio" and not str(url.site)):
        # consumer = _osc.LogFile(File(url, File.WriteOnly), parent=encoder)
        # consumer.subscribeTo(encoder)
    if url.scheme in ("json", "json.udp"):
        endpoint = DataWriter(udp.UdpSender(url), parent=encoder)
        endpoint.subscribeTo(encoder)
    elif url.scheme.endswith("json.tcp"):
        endpoint = encoding.SlipDataWriter(tcp.TcpConnection(url), parent=encoder)
        endpoint.encoderDevice().setOption("nodelay")
        endpoint.subscribeTo(encoder)
    else:
        encoder = None
        print("Unrecognized JSON url:", url)
    return encoder
'''
