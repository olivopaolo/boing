# -*- coding: utf-8 -*-
#
# boing/nodes/NodeLoader.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import os
import traceback
import sys

from PyQt4 import QtCore, QtGui

import boing.nodes.debug as debug
import boing.nodes.encoding as encoding
import boing.nodes.functions as functions
import boing.nodes.logger as logger
import boing.net.tcp as tcp
import boing.net.udp as udp
import boing.utils.fileutils as fileutils 

from boing.core.MappingEconomy import FunctionalNode
from boing.nodes.ioport import DataReader, DataWriter
from boing.nodes.multitouch.ContactViz import ContactViz
from boing.utils.url import URL

if sys.platform=='linux2':
    from boing.nodes.multitouch.MtDevDevice import MtDevDevice


def NodeLoader(url, mode="", **kwargs):
    """Create a new node using the argument "url"."""
    if mode not in ("", "in", "out"): raise ValueError("Invalid mode: %s"%mode)
    if not isinstance(url, URL): url = URL(str(url))

    # -------------------------------------------------------------------
    # IN. AND  OUT. REPLACED USING MODE
    if url.scheme.startswith("in."):
        if mode in ("", "in"):
            url = str(url).replace("in.", "", 1)
            node = NodeLoader(url, "in", **kwargs)
        else:
            raise Exception("Requested node is not an output: %s"%str(url))

    elif url.scheme.startswith("out."):
        if mode in ("", "out"):
            url = str(url).replace("out.", "", 1)
            node = NodeLoader(url, "out", **kwargs)
        else:
            raise Exception("Requested node is not an input: %s"%str(url))

    # -------------------------------------------------------------------
    # UTILS
    elif url.scheme=="dump":
        if mode in ("", "out"):
            kwargs.update(_filterargs(url, "request", "hz"))
            node = debug.DumpNode(**kwargs)
        else:
            raise Exception("Requested node is not an input: %s"%str(url))

    elif url.scheme=="stat":
        if mode in ("", "out"):
            kwargs.update(_filterargs(url, "request", "hz"))
            node = debug.StatProducer(**kwargs)
            node.addObserver(NodeLoader("stdout:", parent=node))
        else:
            raise Exception("Requested node is not an input: %s"%str(url))

    # -------------------------------------------------------------------
    # BRIDGES
    elif url.scheme=="stdin":
        if mode in ("", "in"):
            node = DataReader(fileutils.CommunicationDevice(sys.stdin), **kwargs)
            node.addPost(encoding.TextEncoder(reuse=True))
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
            node.addPost(encoding.TextEncoder(reuse=True) \
                             if inputfile.isTextModeEnabled() \
                             else encoding.TextDecoder(reuse=True))
        elif mode=="out":
            node = DataWriter(
                fileutils.File(url, fileutils.File.WriteOnly), **kwargs)
        elif not mode:
            raise NotImplementedError()

    elif url.scheme=="udp":
        if mode=="in":
            node = DataReader(udp.UdpListener(url), **kwargs)
            node.addPost(encoding.TextDecoder(reuse=True))
        elif mode=="out":
            kwargs.update(_filterargs(url, "writeend"))
            node = DataWriter(udp.UdpSender(url), **kwargs)
        elif not mode:
            raise NotImplementedError()

    elif url.scheme=="tcp":
        if mode=="in":
            node = functions.Filter(**kwargs)
            node.addPost(encoding.TextDecoder(reuse=True))
            server = NodeServer(url.site.host, url.site.port, parent=node)
        elif mode=="out":
            kwargs.update(_filterargs(url, "writeend", "hz"))
            node = DataWriter(tcp.TcpConnection(url), **kwargs)
        elif not mode:
            raise NotImplementedError()

    # -------------------------------------------------------------------
    # SLIP ENCODING
    elif url.scheme.startswith("slip."):
        if mode=="in":
            lower = URL(str(url).replace("slip.", "", 1))
            lower.query.data["uncompress"] = ""
            _validLowerUrl(lower)
            node = NodeLoader(lower, "in", **kwargs)
            node.addPost(
                encoding.SlipDecoder().addPost(
                    encoding.TextDecoder(reuse=True)))
        elif mode=="out":
            lower = URL(str(url).replace("slip.", "", 1))
            _validLowerUrl(lower)
            node = NodeLoader(lower, "out", **kwargs)
            node.addPre(
                encoding.SlipEncoder().addPost(
                    encoding.TextDecoder(reuse=True)))
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
        return NodeLoader(url, mode, **kwargs)

    elif url.scheme=="osc.log":
        if mode=="in":
            kwargs.update(_filterargs(url, "loop", "speed"))
            node = logger.LogPlayer(fileutils.File(url, uncompress=True), 
                                    **kwargs)
            node.addPost(encoding.OscDebug(reuse=True))
            # FIXME: start should be triggered at outputs ready
            QtCore.QTimer.singleShot(300, node.start)
        elif mode=="out":
            kwargs.update(_filterargs(url, "raw"))
            node = logger.LogFile(
                fileutils.File(url, fileutils.File.WriteOnly), **kwargs)
            print("Ctrl-C to stop and close file.")
        elif not mode:
            raise NotImplementedError()            

    elif url.scheme.startswith("osc."):
        if mode=="in":
            lower = URL(str(url).replace("osc.", "", 1))
            _validLowerUrl(lower)
            node = NodeLoader(lower, "in", **kwargs)
            node.addPost(
                encoding.OscDecoder(reuse=True).addPost(
                    encoding.OscDebug(reuse=True)))
        elif mode=="out":
            lower = URL(str(url).replace("osc.", "", 1))
            _validLowerUrl(lower)
            node = NodeLoader(lower, "out", **kwargs)
            node.addPre(
                encoding.OscEncoder(request="osc").addPost(
                    encoding.OscDebug(reuse=True)))
        elif not mode:
            raise NotImplementedError()

    # -------------------------------------------------------------------
    # TUIO ENCODING
    elif url.scheme=="tuio":
        if mode=="in":
            url = URL(str(url))
            if str(url.path): url.scheme += ".osc.log"
            else:
                url.scheme += ".osc.udp"
                if url.site.port==0: url.site.port = 3333
        elif mode=="out":
            url = URL(str(url))
            if str(url.path): url.scheme += ".osc.log"
            elif url.site.host or url.site.port!=0:
                url.scheme += ".osc.udp"
                if not url.site.host: url.site.host="127.0.0.1"
                if url.site.port==0: url.site.port=3333
            else:
                url.scheme += ".stdout" 
        elif not mode:
            raise NotImplementedError()
        print("No transport protocol specified in URL, assuming: %s"%url.scheme)
        return NodeLoader(url, mode, **kwargs)

    elif url.scheme.startswith("tuio."):
        if mode=="in":
            lower = URL(str(url).replace("tuio.", "", 1) \
                if "osc." in url.scheme \
                else str(url).replace("tuio.", "osc.", 1))
            _validLowerUrl(lower)
            node = NodeLoader(lower, "in", **kwargs).addPost(
                encoding.TuioDecoder(reuse=True))
        elif mode=="out":
            lower = URL(str(url).replace("tuio.", "", 1) \
                if "osc." in url.scheme \
                else str(url).replace("tuio.", "osc.", 1))
            _validLowerUrl(lower)
            node = NodeLoader(lower, "out", **kwargs)
            node.addPre(
                encoding.TuioEncoder().addPost(
                    encoding.OscDebug(reuse=True)))
        elif not mode:
            raise NotImplementedError()            

    # -------------------------------------------------------------------
    # MULTI-TOUCH INTERACTION
    elif url.scheme=="mtdev":
        if sys.platform == "linux2":
            if mode in ("", "in"):
                kwargs.update(_filterargs(url))
                node = MtDevDevice(str(url.path), **kwargs)
            else:
                raise Exception("Requested node is not an output: %s"%str(url))
        else:
            raise Exception(
                "'libmtdev' is not available on this platform: %s", sys.platform)

    elif url.scheme=="viz":
        if mode in ("", "out"):
            kwargs.update(_filterargs(url, "antialiasing", "fps", "request"))
            node = ContactViz(**kwargs)
        else:
            raise Exception("Requested node is not an input: %s"%str(url))


    # -------------------------------------------------------------------
    # FUNCTIONS
    elif url.scheme=="calib":
        matrix = None
        args = _filterargs(url, "matrix", "screen")
        if "matrix" in args: matrix = QtGui.QMatrix4x4(args["matrix"])
        elif "screen" in args:
            value = args["screen"]
            if value=="normal": matrix = functions.Calibration.Identity
            elif value=="left": matrix = functions.Calibration.Left
            elif value=="inverted": matrix = functions.Calibration.Inverted
            elif value=="right": matrix = functions.Calibration.Right
        else: matrix = functions.Calibration.Identity
        kwargs.update(_filterargs(url, "args", "request"))
        if "args" not in kwargs: 
            kwargs["args"] = "diff..contacts..rel_pos,rel_speed"
        if "request" not in kwargs: 
            kwargs["request"] = "diff.*.contacts|timetag|source"
        node = functions.Calibration(matrix, reuse=True, **kwargs)

    elif url.scheme=="lag":
        kwargs.update(_filterargs(url, "msec", "request"))
        if "msec" not in kwargs: kwargs["msec"] = 200
        node = functions.Lag(**kwargs)

    elif url.scheme=="filter":
        kwargs.update(_filterargs(url, "request", "hz"))
        node = functions.Filter(**kwargs)

    elif url.scheme=="filterout":
        kwargs.update(_filterargs(url, "out", "request", "hz"))
        node = functions.FilterOut(**kwargs)

    else:
        raise Exception("Invalid URL: %s"%url)

    # -------------------------------------------------------------------
    # POST & PRE ARGS
    kwargs = _filterargs(url)
    for key, value in kwargs.items():
        # Post
        first, partition, end = key.partition("post")
        if first=="" and partition=="post" and (end=="" or end.isdecimal()):
            node.addPost(NodeLoader(value))
        # Pre
        first, partition, end = key.partition("pre")
        if first=="" and partition=="pre" and (end=="" or end.isdecimal()):
            node.addPre(NodeLoader(value))

    return node


class NodeServer(tcp.TcpServer):
    def __init__(self, *args, **kwargs):
        tcp.TcpServer.__init__(self, *args, **kwargs)
        self.newConnection.connect(self.__newConnection)
    def __newConnection(self): 
        conn = self.nextPendingConnection()
        reader = DataReader(conn, parent=conn)
        reader.addObserver(self.parent())


def _filterargs(url, *restrictions):
    rvalue = {}
    for key, value in url.query.data.items():
        if not restrictions or key in restrictions:
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

def _validLowerUrl(url):
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



'''if source is not None:
        filepath = url.query.data.get("conf")
        if filepath is not None:
            # update source's state with the config parameters
            try:
                root = ElementTree.parse(filepath).getroot()
                conf = {}
                for item in root:
                    conf[item.tag] = eval(item.text)
                for key, value in conf.items():
                    statevalue = source.state.get(key)
                    if isinstance(value, dict) \
                       and isinstance(statevalue, dict):
                        copy = statevalue.copy()
                        copy.update(value)
                        conf[key] = copy
                source.setState(**conf)
            except Exception:
                traceback.print_exc()
                print("Cannot load config file", filepath)'''

    
'''if url.kind in (URL.ABSPATH, URL.RELPATH) \
            or url.scheme.startswith("tuio"):        
        output = TuioOutput(url)
    elif url.scheme.startswith("json"):
        output = JSONWriter(url)
    elif url.scheme=="dump":
        req = url.query.data.get('req')
        if req is not None: kwargs["requests"] = parseRequests(req)
        src = url.query.data.get('src')
        if src is not None: kwargs["dumpsrc"] = src.lower()!="false"
        dest = url.query.data.get('dest')
        if dest is not None: kwargs["dumpdest"] = dest.lower()!="false"
        count = url.query.data.get('count')
        if count is not None: kwargs["count"] = count.lower()!="false"
        hz = url.query.data.get('hz')
        if hz is not None:
            try: kwargs["hz"] = float(hz)
            except ValueError: 
                print("ValueError: hz must be numeric, not %s"%
                      hz.__class__.__name__)
        output = DumpNode(**kwargs)
    elif url.scheme=="stat":
        req = url.query.data.get('req')
        if req is not None: kwargs["requests"] = parseRequests(req)
        hz = url.query.data.get('hz')
        if hz is not None:
            try: kwargs["hz"] = float(hz)
            except ValueError: 
                print("ValueError: hz must be numeric, not %s"%
                      hz.__class__.__name__)
        output = StatProducer(**kwargs)
        clear = url.query.data.get('clear')
        clear = clear is not None and clear.lower()!="false"
        writer = _TerminalWriter(clear, output)
        writer.subscribeTo(output)
    elif url.scheme=="viz":
        req = url.query.data.get('req')
        if req is not None: kwargs["requests"] = parseRequests(req)
        if 'hz' in url.query.data:
            hz = url.query.data['hz']
            if hz.lower()=="none": kwargs["fps"] = None
            else:
                try: kwargs["fps"] = float(hz)
                except ValueError: 
                    print("ValueError: hz must be numeric, not %s"%
                          hz.__class__.__name__)
        if "antialiasing" in url.query.data:
            kwargs["antialiasing"] = url.query.data["antialiasing"].lower()!="false"
        output = ContactViz(**kwargs)
        hint = output.sizeHint()
        width = hint.width()
        height = hint. height()
        if 'w' in url.query.data:
            try: 
                width = int(url.query.data['w'])                
            except ValueError: 
                print("ValueError: width must be integer, not %s"%
                      width.__class__.__name__)
        if 'h' in url.query.data:
            try: 
                height = int(url.query.data['h'])
            except ValueError: 
                print("ValueError: height must be integer, not %s"%
                      height.__class__.__name__)
        output.show()
        output.raise_()
        output.resize(width, height)
    elif url.scheme=="buffer":
        req = url.query.data.get('req')
        if req is not None: kwargs["requests"] = parseRequests(req)
        if 'hz' in url.query.data:
            hz = url.query.data['hz']
            if hz.lower()=="none": kwargs["hz"] = None
            else:
                try: kwargs["hz"] = float(hz)
                except ValueError: 
                    print("ValueError: hz must be numeric, not %s"%
                          hz.__class__.__name__)
        output = GestureBuffer(**kwargs)'''

# -------------------------------------------------------------------


'''def TuioSource(url):
    """Return a TuioSource from URL."""
    if not isinstance(url, URL): url = URL(str(url))
    source = TuioToState()
    # Reception time
    rt = url.query.data.get("rt")
    source.rt = rt.lower()!="false" if rt is not None else False
    # Functions
    func = url.query.data.get("func")
    if func is not None:
        functions.addFunctions(source, tuple(s.strip() for s in func.split(",")))
    # Endpoint
    if url.kind in (URL.ABSPATH, URL.RELPATH) \
            or url.scheme=="tuio.file" \
            or (url.scheme=="tuio" and not str(url.site)):
        loop = url.query.data.get("loop")
        speed = url.query.data.get("speed")
        file_ = File(url, File.ReadOnly, uncompress=True)
        player = _osc.LogPlayer(file_, parent=source)
        source.subscribeTo(player)
        if speed:
            try: player.setSpeed(float(speed))
            except: print("Cannot set speed:", speed)
        if loop is not None: player.start(loop.lower!="false")
        else: player.start()
    elif url.scheme in ("tuio", "tuio.udp"):
        socket = DataReader(udp.UdpListener(url), parent=source)
        source.subscribeTo(socket)
    elif url.scheme=="tuio.tcp":
        class ClientWaiter(QtCore.QObject):
            def __init__(self, parent):
                QtCore.QObject.__init__(self, parent)
                self.socket = None
            def newConnection(self): 
                server = self.sender()
                conn = server.nextPendingConnection()
                if not self.socket:
                    reader = encoding.SlipDataReader(conn, parent=source)
                    self.parent().subscribeTo(reader)
                    self.socket = conn
                    self.socket.disconnected.connect(self.disconnected)
                else:
                    conn.close()
            def disconnected(self):
                source = self.parent()
                for o in source.observed():
                    source.unsubscribeFrom(o)
                self.socket = None
        waiter = ClientWaiter(parent=source)
        server = tcp.TcpServer(url.site.host, url.site.port, parent=source)
        server.newConnection.connect(waiter.newConnection)
    else:
        print("WARNING: cannot create TUIO source:", url)
        source = None
    return source
'''
