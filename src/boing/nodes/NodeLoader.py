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

class NodeServer(tcp.TcpServer):
    def __init__(self, *args, **kwargs):
        tcp.TcpServer.__init__(self, *args, **kwargs)
        self.newConnection.connect(self.__newConnection)
    def __newConnection(self): 
        conn = self.nextPendingConnection()
        reader = DataReader(conn, parent=conn)
        reader.addObserver(self.parent())

def NodeLoader(url, option="", getstr=True, **kwargs):
    """Create a new node using the argument "url"."""
    if not isinstance(url, URL): url = URL(str(url))
    node = None

    # -------------------------------------------------------------------
    # UTILS
    if url.scheme=="dump" and option in ("", "out"):
        kwargs.update(_filterargs(url, "request"))
        node = debug.DumpNode(**kwargs)

    elif url.scheme=="stdin" and option in ("", "in"):
        node = DataReader(fileutils.CommunicationDevice(sys.stdin), **kwargs)
        node.addPost(encoding.TextEncoder())

    elif url.scheme=="stdout" and option in ("", "out"):
        node = DataWriter(fileutils.IODevice(sys.stdout), **kwargs)

    elif url.scheme=="stat" and option in ("", "out"):
        kwargs.update(_filterargs(url, "request"))
        node = debug.StatProducer(**kwargs)
        node.addObserver(NodeLoader("stdout:", parent=node))

    # -------------------------------------------------------------------
    # BRIDGES
    elif url.scheme in ("", "file") and option=="in" \
            or url.scheme=="in.file" and option==("", "in"):
        filepath = str(url.path)
        if os.path.isfile(filepath):
            file_ = fileutils.FileReader(url, **_filterargs(url, "uncompress"))
            # FIXME: start should be triggered at outputs ready
            QtCore.QTimer.singleShot(300, file_.start)
        elif os.path.exists(filepath):            
            file_ = fileutils.CommunicationFile(url)
        else:
            file_ = None
            print("ERROR! Cannot open requested file:", filepath)
        if file_ is not None:
            node = DataReader(file_, **kwargs)
            node.addPost(encoding.TextEncoder() \
                             if file_.isTextModeEnabled() \
                             else encoding.TextDecoder())

    elif url.scheme in ("", "file") and option=="out" \
            or url.scheme=="out.file" and option in ("", "out"):
        try:
            node = DataWriter(fileutils.File(url, fileutils.File.WriteOnly),
                              **kwargs)
        except IOError:
            print("ERROR! Cannot write to file:", str(url.path))

    elif url.scheme=="udp" and option=="in" \
            or url.scheme=="in.udp" and option in ("", "in"):
        node = DataReader(udp.UdpListener(url), **kwargs)
        if getstr: node.addPost(encoding.TextDecoder())

    elif url.scheme=="udp" and option=="out" \
            or url.scheme=="out.udp" and option==("", "out"):
        node = DataWriter(udp.UdpSender(url), **kwargs)

    elif url.scheme=="tcp" and option=="in" \
            or url.scheme=="in.tcp" and option==("", "in"):
        node = functions.Filter(**kwargs)
        if getstr: node.addPost(encoding.TextDecoder())
        server = NodeServer(url.site.host, url.site.port, parent=node)

    elif url.scheme=="tcp" and option=="out" \
            or url.scheme=="out.tcp" and option==("", "out"):
        node = DataWriter(tcp.TcpConnection(url), **kwargs)

    # -------------------------------------------------------------------
    # SLIP ENCODING
    elif url.scheme.startswith("slip.") and option=="in":
        node = encoding.SlipDecoder(**kwargs)
        if getstr: node.addPost(encoding.TextDecoder())
        url = URL(str(url))
        url.scheme = url.scheme.replace("slip.", "")
        url.query.data["uncompress"] = ""
        reader = NodeLoader(url, "in", parent=node)
        reader.addObserver(node)

    elif url.scheme.startswith("slip.") and option=="out":
        node = encoding.SlipEncoder(**kwargs)
        url = URL(str(url))
        url.scheme = url.scheme.replace("slip.", "")
        port = NodeLoader(url, "out", parent=node)
        port.subscribeTo(node)

    # -------------------------------------------------------------------
    # OSC ENCODING
    elif url.scheme in ("osc", "in.osc", "out.osc"):
        url = URL(str(url))
        if not str(url.path): url.scheme += ".udp"
        else: 
            url.scheme += ".slip.file"
            url.query.data["uncompress"] = ""
        print("No transport protocol specified in URL, assuming: %s"%url.scheme)
        node = NodeLoader(url, option, **kwargs)

    elif url.scheme.startswith("osc.") and option=="in":
        # TODO: handle in.osc.
        url = URL(str(url))
        url.scheme = url.scheme.replace("osc.", "")
        url.query.data["uncompress"] = ""
        node = NodeLoader(url, "in", getstr=False)
        oscdecoder = encoding.OscDecoder(**kwargs)
        if getstr: oscdecoder.addPost(encoding.OscDebug())
        node.addPost(oscdecoder)

    elif url.scheme.startswith("osc.") and option=="out":
        # TODO: handle out.osc.
        node = encoding.OscEncoder(forward=True, **kwargs)
        if getstr: node.addPost(encoding.OscDebug())
        url = URL(str(url))
        url.scheme = url.scheme.replace("osc.", "")
        transport = NodeLoader(url, "out", parent=node)
        transport.subscribeTo(node)

    # -------------------------------------------------------------------
    # TUIO ENCODING
    elif url.scheme=="tuio" and option=="in" \
            or url.scheme=="in.tuio" and option in ("", "in"):
        url = URL(str(url))
        if not str(url.path): 
            url.scheme += ".udp"
            if not url.site.host and url.site.port==0: url.site.port = 3333
        else: 
            url.scheme += ".slip.file"
            url.query.data["uncompress"] = ""
        print("No transport protocol specified in URL, assuming: %s"%url.scheme)
        node = NodeLoader(url, option, **kwargs)
        
    elif url.scheme=="tuio" and option=="out" \
            or url.scheme=="out.tuio" and option in ("", "out"):
        url = URL(str(url))
        if not str(url.path) and url.site.port==0: url.scheme += ".stdout" 
        else: 
            url.scheme += ".slip.file"
        print("No transport protocol specified in URL, assuming: %s"%url.scheme)
        node = NodeLoader(url, option, **kwargs)

    elif url.scheme.startswith("tuio.") and option=="in":
        # TODO: handle in.tuio.
        url = URL(str(url))
        url.scheme = url.scheme.replace("tuio.", "")
        url.scheme = url.scheme.replace("osc.", "")
        url.query.data["uncompress"] = ""
        node = NodeLoader(url, "in", getstr=False)
        oscdecoder = encoding.OscDecoder(**kwargs)
        if getstr: oscdecoder.addPost(encoding.OscDebug())
        oscdecoder.addPost(encoding.TuioDecoder(**kwargs))
        node.addPost(oscdecoder)

    elif url.scheme.startswith("tuio.") and option=="out":
        # TODO: handle out.tuio.
        node = encoding.TuioEncoder(**kwargs)
        oscencoder = encoding.OscEncoder()
        if getstr: node.addPost(encoding.OscDebug())
        url = URL(str(url))
        url.scheme = url.scheme.replace("tuio.", "")
        url.scheme = url.scheme.replace("osc.", "")
        url.query.data["uncompress"] = ""
        transport = NodeLoader(url, "out", parent=node)
        transport.subscribeTo(node)

    # -------------------------------------------------------------------
    # RECORD/REPLAY
    elif url.scheme=="log.osc" and option in ("", "out"):
        try:
            kwargs.update(_filterargs(url, "raw"))
            node = logger.LogFile(
                fileutils.File(url, fileutils.File.WriteOnly), **kwargs)
        except IOError:
            print("Cannot write to file:", str(url.path))

    elif url.scheme in ("out.log.tuio", "log.tuio"):
        try:
            node = encoding.TuioEncoder(**kwargs).addPost(encoding.OscEncoder)
            node.addObserver(
                logger.LogFile(fileutils.File(url, fileutils.File.WriteOnly)),
                parent=Node)
        except IOError:
            print("Cannot write to file:", str(url.path))

    elif url.scheme=="play.osc" and option in ("", "in"):
        filepath = str(url.path)
        if os.path.isfile(filepath):
            node = logger.LogPlayer(
                fileutils.File(url, fileutils.File.ReadOnly, uncompress=True),
                **kwargs)
            if getstr: node.addPost(encoding.OscDebug())
            args = _filterargs(url, "loop", "speed")
            node.setSpeed(args.get("speed", 1))
            # FIXME: start should be triggered at outputs ready
            QtCore.QTimer.singleShot(
                    300, lambda: node.start(kwargs.get("loop", False)))
        else:
            print("ERROR! Cannot open requested file:", filepath)
        
    elif url.scheme=="play.tuio" and option in ("", "in"):
        filepath = str(url.path)
        if os.path.isfile(filepath):
            node = logger.LogPlayer(
                fileutils.File(url, fileutils.File.ReadOnly, uncompress=True),
                **kwargs)
            if getstr: node.addPost(encoding.OscDebug())
            args = _filterargs(url, "loop", "speed")
            node.setSpeed(args.get("speed", 1))
            # FIXME: start should be triggered at outputs ready
            QtCore.QTimer.singleShot(
                    300, lambda: node.start(kwargs.get("loop", False)))
            node.addPost(encoding.TuioDecoder(**_filterargs(url, "rt")))
        else:
            print("Cannot open file:", filepath)

    # -------------------------------------------------------------------
    # MULTI-TOUCH INTERACTION
    elif url.scheme=="mtdev" and option in ("", "in"):
        if sys.platform == "linux2":
            try:
                node = MtDevDevice(str(url.path), **kwargs)
            except Exception:
                traceback.print_exc()
        else:
            print("ERROR! 'libmtdev' is not available on this platform:", 
                  sys.platform)

    elif url.scheme=="viz" and option in ("", "out"):
        node = ContactViz(**kwargs)

    # -------------------------------------------------------------------
    # FUNCTIONS
        '''elif url.scheme in ("calib", "out.calib"):
        matrix = None
        kwargs = _filterargs(url, "matrix", "screen")
        if "matrix" in kwargs:
            matrix = QtGui.QMatrix4x4(kwargs["matrix"])
        elif "screen" in kwargs:
            value = kwargs["screen"]
            if value=="normal": matrix = functions.Calibration.Identity
            if value=="left": matrix = functions.Calibration.Left
            if value=="inverted": matrix = functions.Calibration.Inverted
            if value=="right": matrix = functions.Calibration.Right
        else: matrix = functions.Calibration.Identity
        kwargs = _filterargs(url, "args", "request")
        if "args" not in kwargs: kwargs["args"] = "$..rel_pos,rel_speed"            
        if "request" not in kwargs: 
            kwargs["request"] = "diff.*.contacts|timetag|source"
        node = functions.Calibration(matrix, **kwargs)
        kwargs = _filterargs(url)
        for key, value in kwargs.items():
            first, partition, end = key.partition("out")
            if first=="" and partition=="out" and (end=="" or end.isdecimal()):
                post = NodeLoader(value)
                if post is not None: node.addPost(post)

    elif url.scheme in ("lag", "out.lag"):
        kwargs = _filterargs(url, "msec", "request")
        if "msec" not in kwargs: kwargs["msec"] = 200
        node = functions.Lag(**kwargs)
        kwargs = _filterargs(url)
        for key, value in kwargs.items():
            first, partition, end = key.partition("out")
            if first=="" and partition=="out" and (end=="" or end.isdecimal()):
                post = NodeLoader(value)
                if post is not None: node.addPost(post)

    elif url.scheme in ("sieve", "out.sieve"):
        kwargs = _filterargs(url, "request")
        node = functions.Filter(**kwargs)
        kwargs = _filterargs(url)
        for key, value in kwargs.items():
            first, partition, end = key.partition("out")
            if first=="" and partition=="out" and (end=="" or end.isdecimal()):
                post = NodeLoader(value)
                if post is not None: node.addPost(post)'''

    else:
        print("Invalid URL:", url)
    return node


def _filterargs(url, *restrictions):
    rvalue = {}
    for key, value in url.query.data.items():
        if not restrictions or key in restrictions:
            rvalue[key] = _kwstr2value(url.query.data[key])
    return rvalue

def _kwstr2value(string):
    if string=="": rvalue = True
    elif string.lower()=="none": rvalue = None
    elif string.isdecimal(): rvalue = int(string)
    else:
        try:
            rvalue = float(string)
        except ValueError: 
            rvalue = string
    return rvalue


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
