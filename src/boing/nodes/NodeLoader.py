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

from boing.nodes.ioport import DataReader, DataWriter
from boing.nodes.multitouch.ContactViz import ContactViz
from boing.nodes.multitouch.MtDevDevice import MtDevDevice
from boing.utils.url import URL


class NodeServer(tcp.TcpServer):
    def __init__(self, *args, **kwargs):
        tcp.TcpServer.__init__(self, *args, **kwargs)
        self.newConnection.connect(self.__newConnection)
    def __newConnection(self): 
        conn = self.nextPendingConnection()
        reader = DataReader(conn, parent=conn)
        reader.addObserver(self.parent())


def NodeLoader(url):
    """Create a new node using the argument "url"."""
    if not isinstance(url, URL): url = URL(str(url))
    node = None

    if url.scheme in ("dump", "out.dump"):
        kwargs = _urlquery2kwargs(url, "request")
        node = debug.DumpNode(**kwargs)

    elif url.scheme in ("stdin", "in.stdin"):
        node = DataReader(fileutils.CommunicationDevice(sys.stdin))
        node.addPost(encoding.TextEncoder())

    elif url.scheme in ("stdout", "out.stdout"):
        node = DataWriter(fileutils.IODevice(sys.stdout))

    elif url.scheme in ("stat", "out.stat"):
        kwargs = _urlquery2kwargs(url, "request")
        node = debug.StatProducer(**kwargs)
        node.addObserver(DataWriter(fileutils.IODevice(sys.stdout), 
                                    parent=node))

    elif url.scheme in ("viz", "out.viz"):
        node = ContactViz()

    elif url.scheme in ("in", "in.file"):
        filepath = str(url.path)
        if os.path.isfile(filepath):
            kwargs = _urlquery2kwargs(url, "uncompress")
            file_ = fileutils.FileReader(url, **kwargs)
            # FIXME: start should be triggered at outputs ready
            QtCore.QTimer.singleShot(300, file_.start)
        elif os.path.exists(filepath):            
            file_ = fileutils.CommunicationFile(url)
        else:
            print("Cannot open file:", filepath)
            file_ = None
        if file_ is not None:
            node = DataReader(file_)
            node.addPost(encoding.TextEncoder() \
                             if node.inputDevice().isTextModeEnabled() \
                             else encoding.TextDecoder())

    elif url.scheme in ("out", "out.file"):
        try:
            node = DataWriter(fileutils.File(url, fileutils.File.WriteOnly))
        except IOError:
            print("Cannot write to file:", str(url.path))

    elif url.scheme=="in.udp":
        node = DataReader(udp.UdpListener(url))
        node.addPost(encoding.TextDecoder())

    elif url.scheme=="out.udp":
        node = DataWriter(udp.UdpSender(url))

    elif url.scheme=="in.slip.udp":
        node = encoding.SlipDecoder().addPost(encoding.TextDecoder())
        node.subscribeTo(DataReader(udp.UdpListener(url), parent=node))
    elif url.scheme=="out.slip.udp":
        node = encoding.SlipEncoder()
        node.addObserver(DataWriter(udp.UdpSender(url), parent=node))

    elif url.scheme=="in.tcp":
        node = functions.Filter().addPost(encoding.TextDecoder())
        server = NodeServer(url.site.host, url.site.port, parent=node)
    elif url.scheme=="out.tcp":
        node = DataWriter(tcp.TcpConnection(url))

    elif url.scheme=="in.slip.tcp":
        node = encoding.SlipDecoder().addPost(encoding.TextDecoder())
        server = NodeServer(url.site.host, url.site.port, parent=node)
    elif url.scheme=="out.slip.tcp":
        node = encoding.SlipEncoder()
        node.addObserver(DataWriter(tcp.TcpConnection(url), parent=node))
        
    elif url.scheme in ("in.osc"): #, "out.osc"):
        url = URL(str(url))
        if str(url.path)=="":
            url.scheme += ".udp"
        else: 
            url.scheme += ".slip.file"
            url.query.data["uncompress"] = ""
        print("No transport protocol specified in URL, assuming: %s"%url.scheme)
        node = NodeLoader(url)

    elif url.scheme=="in.osc.udp":
        node = DataReader(udp.UdpListener(url)).addPost(
            encoding.OscDecoder().addPost(encoding.OscDebug()))
        '''elif url.scheme=="out.osc.udp":
        node = DataWriter(udp.UdpSender(url))'''

    elif url.scheme=="in.osc.tcp":
        node = encoding.SlipDecoder()
        node.addPost(encoding.OscDecoder().addPost(encoding.OscDebug()))
        server = NodeServer(url.site.host, url.site.port, parent=node)
        '''elif url.scheme=="out.osc.udp":
        node = encoding.SlipEncoder()
        node.addObserver(DataWriter(tcp.TcpConnection(url), parent=node))'''

    elif url.scheme=="in.osc.slip.tcp":
        node = encoding.SlipDecoder()
        node.addPost(encoding.OscDecoder().addPost(encoding.OscDebug()))
        server = NodeServer(url.site.host, url.site.port, parent=node)
        '''elif url.scheme=="out.osc.slip.tcp":
        node = encoding.SlipEncoder()
        node.addObserver(DataWriter(tcp.TcpConnection(url), parent=node))'''
        
    elif url.scheme=="in.osc.slip.file":
        filepath = str(url.path)
        if os.path.isfile(filepath):
            kwargs = _urlquery2kwargs(url)
            file_ = fileutils.FileReader(url, **kwargs)
            # FIXME: start should be triggered at outputs ready
            QtCore.QTimer.singleShot(300, file_.start)
            node = encoding.SlipDecoder()
            node.subscribeTo(DataReader(file_, parent=node))
            node.addPost(encoding.OscDecoder().addPost(encoding.OscDebug()))
        else:
            print("Cannot open file:", filepath)
        '''elif url.scheme=="out.osc.slip.file":
        try:
            node = encoding.SlipEncoder()
            node.addObserver(DataWriter(fileutils.File(url, fileutils.File.WriteOnly), parent=node))
        except IOError:
            print("Cannot write to file:", str(url.path))
            node = None'''

    elif url.scheme=="in.tuio":
        url = URL(str(url))
        if str(url.path)=="":
            url.scheme += ".udp"
            if url.site.host=="" and url.site.port==0: url.site.port = 3333
        else: 
            url.scheme += ".slip.file"
            url.query.data["uncompress"] = ""
        print("No transport protocol specified in URL, assuming: %s"%url.scheme)
        node = NodeLoader(url)

    elif url.scheme=="out.tuio":
        url = URL(str(url))
        if url.site.host=="" and url.site.port==0: url.scheme += ".stdout"
        else:
            url.scheme += ".udp"
            if url.site.host=="": url.site.host = "::1"
            if url.site.port==0: url.site.port = 3333
        print("No transport protocol specified in URL, assuming: %s"%url.scheme)
        node = NodeLoader(url)

    elif url.scheme=="in.tuio.udp":
        oscdecoder = encoding.OscDecoder().addPost(encoding.OscDebug())
        kwargs = _urlquery2kwargs(url, "rt")        
        oscdecoder.addPost(encoding.TuioDecoder(**kwargs))
        node = DataReader(udp.UdpListener(url)).addPost(oscdecoder)

    elif url.scheme=="out.tuio.udp":
        node = encoding.TuioEncoder()
        node.addObserver(
            encoding.OscEncoder(parent=node).addPost(DataWriter(udp.UdpSender(url))))

    elif url.scheme=="out.tuio.udp":
        node = encoding.TuioEncoder()
        node.addObserver(
            encoding.OscEncoder(parent=node).addPost(DataWriter(udp.UdpSender(url))))

    elif url.scheme=="out.tuio.stdout":
        node = encoding.TuioEncoder()
        node.addObserver(
            encoding.OscDebug(parent=node).addPost(DataWriter(fileutils.IODevice(sys.stdout))))

    elif url.scheme in ("in.play.osc", "play.osc"):
        filepath = str(url.path)
        if os.path.isfile(filepath):
            file_ = fileutils.File(url, fileutils.File.ReadOnly, uncompress=True)
            kwargs = _urlquery2kwargs(url, "loop", "speed")
            node = logger.LogPlayer(file_).addPost(encoding.OscDebug())
            if "speed" in kwargs: node.setSpeed(kwargs["speed"])
            # FIXME: start should be triggered at outputs ready
            loop = kwargs.get("loop", False)
            QtCore.QTimer.singleShot(300, lambda: node.start(loop))
        else:
            print("Cannot open file:", filepath)

    elif url.scheme in ("in.play.tuio", "play.tuio"):
        filepath = str(url.path)
        if os.path.isfile(filepath):
            file_ = fileutils.File(url, fileutils.File.ReadOnly, uncompress=True)
            kwargs = _urlquery2kwargs(url, "rt")
            node = logger.LogPlayer(file_).addPost(encoding.OscDebug())
            node.addPost(encoding.TuioDecoder(**kwargs))
            kwargs = _urlquery2kwargs(url, "loop", "speed")
            if "speed" in kwargs: node.setSpeed(kwargs["speed"])
            # FIXME: start should be triggered at outputs ready
            loop = kwargs.get("loop", False)
            QtCore.QTimer.singleShot(300, lambda: node.start(loop))
        else:
            print("Cannot open file:", filepath)

    elif url.scheme in ("out.log.osc", "log.osc"):
        try:
            kwargs = _urlquery2kwargs(url, "raw")
            node = logger.LogFile(fileutils.File(url, fileutils.File.WriteOnly), **kwargs)
        except IOError:
            print("Cannot write to file:", str(url.path))
            node = None

    elif url.scheme in ("out.log.tuio", "log.tuio"):
        try:
            node = encoding.TuioEncoder()
            node.addObserver(
                encoding .OscEncoder(parent=node).addPost(
                    logger.LogFile(fileutils.File(url, fileutils.File.WriteOnly))))
        except IOError:
            print("Cannot write to file:", str(url.path))
            node = None

    elif url.scheme in ("in.mtdev", "mtdev"):
        try:
            node = MtDevDevice(str(url.path))
        except Exception:
            traceback.print_exc()

        '''elif url.scheme in ("calib", "out.calib"):
        matrix = None
        kwargs = _urlquery2kwargs(url, "matrix", "screen")
        if "matrix" in kwargs:
            matrix = QtGui.QMatrix4x4(kwargs["matrix"])
        elif "screen" in kwargs:
            value = kwargs["screen"]
            if value=="normal": matrix = functions.Calibration.Identity
            if value=="left": matrix = functions.Calibration.Left
            if value=="inverted": matrix = functions.Calibration.Inverted
            if value=="right": matrix = functions.Calibration.Right
        else: matrix = functions.Calibration.Identity
        kwargs = _urlquery2kwargs(url, "args", "request")
        if "args" not in kwargs: kwargs["args"] = "$..rel_pos,rel_speed"            
        if "request" not in kwargs: 
            kwargs["request"] = "diff.*.contacts|timetag|source"
        node = functions.Calibration(matrix, **kwargs)
        kwargs = _urlquery2kwargs(url)
        for key, value in kwargs.items():
            first, partition, end = key.partition("out")
            if first=="" and partition=="out" and (end=="" or end.isdecimal()):
                post = NodeLoader(value)
                if post is not None: node.addPost(post)

    elif url.scheme in ("lag", "out.lag"):
        kwargs = _urlquery2kwargs(url, "msec", "request")
        if "msec" not in kwargs: kwargs["msec"] = 200
        node = functions.Lag(**kwargs)
        kwargs = _urlquery2kwargs(url)
        for key, value in kwargs.items():
            first, partition, end = key.partition("out")
            if first=="" and partition=="out" and (end=="" or end.isdecimal()):
                post = NodeLoader(value)
                if post is not None: node.addPost(post)

    elif url.scheme in ("sieve", "out.sieve"):
        kwargs = _urlquery2kwargs(url, "request")
        node = functions.Filter(**kwargs)
        kwargs = _urlquery2kwargs(url)
        for key, value in kwargs.items():
            first, partition, end = key.partition("out")
            if first=="" and partition=="out" and (end=="" or end.isdecimal()):
                post = NodeLoader(value)
                if post is not None: node.addPost(post)'''

    else:
        print("Invalid URL:", url)
    return node


def _urlquery2kwargs(url, *restrictions):
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



#if sys.platform=='linux2':
#    from boing.multitouch.MtDevDevice import MtDevDevice

'''if url.kind in (URL.ABSPATH, URL.RELPATH) \
            or url.scheme.startswith("tuio"): 
        source = TuioSource(url)
    elif url.scheme.startswith("json"):
        source = JSONReader(url)
    elif url.scheme.startswith("mtdev"):
        if sys.platform == "linux2":
            try:
                source = MtDevDevice(str(url.path))
            except Exception:
                traceback.print_exc()
            else:
                # Functions
                func = url.query.data.get("func")
                if func is not None:
                    functions.addFunctions(
                        source, tuple(s.strip() for s in func.split(",")))
        else:
            print("mtdev devices are not supported on ", sys.platform)'''
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
