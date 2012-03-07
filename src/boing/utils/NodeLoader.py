# -*- coding: utf-8 -*-
#
# boing/utils/NodeLoader.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import os
import sys

from PyQt4 import QtCore

from boing.eventloop.MappingEconomy import DumpConsumer, IdentityNode
from boing.multitouch.ContactViz import ContactViz
from boing.slip.SlipDataIO import SlipEncoder, SlipDecoder
from boing.osc.logging import LogFile, LogPlayer
from boing.osc.encoding import OscEncoder, OscDecoder, OscDebug
from boing.tcp.TcpServer import TcpServer
from boing.tcp.TcpSocket import TcpConnection
from boing.tuio.TuioToState import TuioToState
from boing.udp.UdpSocket import UdpSender, UdpListener
from boing.utils.IODevice import IODevice, CommunicationDevice
from boing.utils.DataIO import DataReader, DataWriter, DataIO
from boing.utils.File import File, FileReader, CommunicationFile
from boing.utils.debug import RenameNode, StatProducer
from boing.utils.TextIO import TextEncoder, TextDecoder
from boing.url import URL


class NodeServer(TcpServer):
    def __init__(self, *args, **kwargs):
        TcpServer.__init__(self, *args, **kwargs)
        self.newConnection.connect(self.__newConnection)
    def __newConnection(self): 
        conn = self.nextPendingConnection()
        reader = DataReader(conn, parent=conn)
        reader.addObserver(self.parent())


def NodeLoader(url):
    """Create a new node using the argument "url"."""
    _url = url if isinstance(url, URL) else URL(str(url))
    node = None

    if _url.scheme in ("dump", "out.dump"):
        kwargs = _urlquery2kwargs(url, "request")
        node = DumpConsumer(**kwargs)

    elif _url.scheme in ("stdin", "in.stdin"):
        node = DataReader(CommunicationDevice(sys.stdin)).addPost(TextEncoder())

    elif _url.scheme in ("stdout", "out.stdout"):
        node = DataWriter(IODevice(sys.stdout))

    elif _url.scheme in ("stat", "out.stat"):
        kwargs = _urlquery2kwargs(url, "request")
        node = StatProducer(**kwargs)
        node.addObserver(DataWriter(IODevice(sys.stdout), parent=node))

    elif _url.scheme in ("viz", "out.viz"):
        node = ContactViz()
        node.show()

    elif _url.scheme in ("in", "in.file"):
        filepath = str(_url.path)
        if os.path.isfile(filepath):
            kwargs = _urlquery2kwargs(_url, "uncompress")
            file_ = FileReader(_url, **kwargs)
            # FIXME: start should be triggered at outputs ready
            QtCore.QTimer.singleShot(300, file_.start)
        elif os.path.exists(filepath):            
            file_ = CommunicationFile(_url)
        else:
            print("Cannot open file:", filepath)
            file_ = None
        if file_ is not None:
            node = DataReader(file_)
            node.addPost(TextEncoder() if node.inputDevice().isTextModeEnabled() \
                             else TextDecoder())
    elif _url.scheme in ("out", "out.file"):
        try:
            node = DataWriter(File(_url, File.WriteOnly))
        except IOError:
            print("Cannot write to file:", str(_url.path))

    elif _url.scheme=="in.udp":
        node = DataReader(UdpListener(_url)).addPost(TextDecoder())
    elif _url.scheme=="out.udp":
        node = DataWriter(UdpSender(_url))

    elif _url.scheme=="in.slip.udp":
        node = SlipDecoder().addPost(TextDecoder())
        node.subscribeTo(DataReader(UdpListener(_url), parent=node))
    elif _url.scheme=="out.slip.udp":
        node = SlipEncoder()
        node.addObserver(DataWriter(UdpSender(_url), parent=node))

    elif _url.scheme=="in.tcp":
        node = IdentityNode().addPost(TextDecoder())
        server = NodeServer(_url.site.host, _url.site.port, parent=node)
    elif _url.scheme=="out.tcp":
        node = DataWriter(TcpConnection(_url))

    elif _url.scheme=="in.slip.tcp":
        node = SlipDecoder().addPost(TextDecoder())
        server = NodeServer(_url.site.host, _url.site.port, parent=node)
    elif _url.scheme=="out.slip.tcp":
        node = SlipEncoder()
        node.addObserver(DataWriter(TcpConnection(_url), parent=node))
        
    elif _url.scheme in ("in.osc"): #, "out.osc"):
        _url = URL(str(_url))
        if str(_url.path)=="":
            _url.scheme += ".udp"
        else: 
            _url.scheme += ".slip.file"
            _url.query.data["uncompress"] = ""
        print("No transport protocol specified in URL, assuming: %s"%_url.scheme)
        node = NodeLoader(_url)

    elif _url.scheme=="in.osc.udp":
        node = DataReader(UdpListener(_url)).addPost(
            OscDecoder().addPost(OscDebug()))
        '''elif _url.scheme=="out.osc.udp":
        node = DataWriter(UdpSender(_url))'''

    elif _url.scheme=="in.osc.tcp":
        node = SlipDecoder().addPost(OscDecoder().addPost(OscDebug()))
        server = NodeServer(_url.site.host, _url.site.port, parent=node)
        '''elif _url.scheme=="out.osc.udp":
        node = SlipEncoder()
        node.addObserver(DataWriter(TcpConnection(_url), parent=node))'''

    elif _url.scheme=="in.osc.slip.tcp":
        node = SlipDecoder().addPost(OscDecoder().addPost(OscDebug()))
        server = NodeServer(_url.site.host, _url.site.port, parent=node)
        '''elif _url.scheme=="out.osc.slip.tcp":
        node = SlipEncoder()
        node.addObserver(DataWriter(TcpConnection(_url), parent=node))'''
        
    elif _url.scheme=="in.osc.slip.file":
        filepath = str(_url.path)
        if os.path.isfile(filepath):
            kwargs = _urlquery2kwargs(_url)
            file_ = FileReader(_url, **kwargs)
            # FIXME: start should be triggered at outputs ready
            QtCore.QTimer.singleShot(300, file_.start)
            node = SlipDecoder()
            node.subscribeTo(DataReader(file_, parent=node))
            node.addPost(OscDecoder().addPost(OscDebug()))
        else:
            print("Cannot open file:", filepath)
        '''elif _url.scheme=="out.osc.slip.file":
        try:
            node = SlipEncoder()
            node.addObserver(DataWriter(File(_url, File.WriteOnly), parent=node))
        except IOError:
            print("Cannot write to file:", str(_url.path))
            node = None'''

    elif _url.scheme=="in.tuio":
        _url = URL(str(_url))
        if str(_url.path)=="":
            _url.scheme += ".udp"
            if _url.site.host=="" and _url.site.port==0: _url.site.port = 3333
        else: 
            _url.scheme += ".slip.file"
            _url.query.data["uncompress"] = ""
        print("No transport protocol specified in URL, assuming: %s"%_url.scheme)
        node = NodeLoader(_url)

    elif _url.scheme=="in.tuio.udp":
        kwargs = _urlquery2kwargs(url, "rt")                
        node = DataReader(UdpListener(_url)).addPost(
            OscDecoder().addPost(OscDebug()).addPost(TuioToState(**kwargs)))

    elif _url.scheme in ("in.play.osc", "play.osc"):
        filepath = str(_url.path)
        if os.path.isfile(filepath):
            file_ = File(_url, File.ReadOnly, uncompress=True)
            kwargs = _urlquery2kwargs(_url, "loop", "speed")
            node = LogPlayer(file_).addPost(OscDebug())
            if "speed" in kwargs: node.setSpeed(kwargs["speed"])
            # FIXME: start should be triggered at outputs ready
            loop = kwargs.get("loop", False)
            QtCore.QTimer.singleShot(300, lambda: node.start(loop))
        else:
            print("Cannot open file:", filepath)

    elif _url.scheme in ("in.play.tuio", "play.tuio"):
        filepath = str(_url.path)
        if os.path.isfile(filepath):
            file_ = File(_url, File.ReadOnly, uncompress=True)
            kwargs = _urlquery2kwargs(_url, "rt")
            node = LogPlayer(file_).addPost(OscDebug()).addPost(TuioToState(**kwargs))
            kwargs = _urlquery2kwargs(_url, "loop", "speed")
            if "speed" in kwargs: node.setSpeed(kwargs["speed"])
            # FIXME: start should be triggered at outputs ready
            loop = kwargs.get("loop", False)
            QtCore.QTimer.singleShot(300, lambda: node.start(loop))
        else:
            print("Cannot open file:", filepath)

    elif _url.scheme in ("out.log.osc", "log.osc"):
        try:
            kwargs = _urlquery2kwargs(_url, "raw")
            node = LogFile(File(_url, File.WriteOnly), **kwargs)
        except IOError:
            print("Cannot write to file:", str(_url.path))
            node = None

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
        endpoint = DataReader(UdpListener(url), parent=decoder)
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
                    reader = SlipDataReader(conn, parent=decoder)
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
        server = TcpServer(url.site.host, url.site.port, parent=decoder)
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
        # consumer = LogFile(File(url, File.WriteOnly), parent=encoder)
        # consumer.subscribeTo(encoder)
    if url.scheme in ("json", "json.udp"):
        endpoint = DataWriter(UdpSender(url), parent=encoder)
        endpoint.subscribeTo(encoder)
    elif url.scheme.endswith("json.tcp"):
        endpoint = SlipDataWriter(TcpConnection(url), parent=encoder)
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




'''from boing.eventloop.OnDemandProduction import DumpConsumer
from boing.multitouch.GestureBuffer import GestureBuffer
from boing.multitouch.ContactViz import ContactViz
from boing.eventloop.MappingEconomy import parseRequests
from boing.json.JSONTunnel import JSONWriter
from boing.tuio.StateToTuio import TuioOutput
from boing.utils.IODevice import IODevice
from boing.utils.StatProducer import StatProducer
from boing.utils.TextIO import TextWriter'''

    
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
        output = DumpConsumer(**kwargs)
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
