# -*- coding: utf-8 -*-
#
# boing/tuio/TuioToState.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from datetime import datetime

from PyQt4.QtCore import QObject

from boing import osc, tuio
from boing.eventloop.OnDemandProduction import SelectiveConsumer
from boing.eventloop.StateMachine import StateMachine
from boing.eventloop.MappingEconomy import MappingProducer
from boing.osc.LogPlayer import LogPlayer
from boing.slip.SlipDataIO import SlipDataReader
from boing.tcp.TcpServer import TcpServer
from boing.udp.UdpSocket import UdpListener
from boing.utils.ExtensibleTree import ExtensibleTree
from boing.utils.DataIO import DataReader
from boing.utils.File import File
from boing.url import URL

class TuioToState(StateMachine, SelectiveConsumer):
    """Based on the TUIO 1.1 Protocol Specification
    http://www.tuio.org/?specification
    
    It will not work if inside an OSC bundle there is data from more
    than one source or for more than one TUIO profile."""

    def __init__(self, parent=None):
        StateMachine.__init__(self, 
                              productoffer={("diff",".*","gestures"),
                                            "osc", "data"},
                              parent=parent)
        SelectiveConsumer.__init__(self, requests={"osc", "data"})
        """Alive TUIO items."""
        # self.__alive[source][profile] = set of session_ids
        self.__alive = {}
        """Association between the TUIO Session ID and the gesture event ID.
        This is necessary because different TUIO sources may use the same
        Session ID."""
        # self.__idpairs[source][session_id] = event_id
        self.__idpairs = {}
        self.__idcount = 0
        """If rt is True, the event is tagged using the timestamp at
        the event creation instead of using the OSC bundle time tag."""
        self.rt = False
        self._postosc = False
        self._postdata = False
        # Setup initial state
        self._state.gestures

    def __del__(self):
        StateMachine.__del__(self)
        SelectiveConsumer.__del__(self)

    def _checkRef(self):
        StateMachine._checkRef(self)
        SelectiveConsumer._checkRef(self)

    def _updateOverallDemand(self):
        StateMachine._updateOverallDemand(self)
        self._postosc = MappingProducer.match("osc", self._overalldemand)
        self._postdata = MappingProducer.match("data", self._overalldemand)

    def _consume(self, products, producer):
        for p in products:
            packet = None
            if "osc" in p: 
                packet = p["osc"]
                data = p["data"] if "data" in p else None
            elif "data" in p:
                data = p["data"]
                packet = osc.decode(data) if data else None
            if isinstance(packet, osc.Bundle): 
                self.__handleOsc(packet, data)

    def __handleOsc(self, packet, data):
        timetag = datetime.now() if self.rt else packet.timetag
        source = fseq = profile = None
        desc = {}
        alive = set()
        for msg in packet.elements:
            if msg.address.startswith("/tuio/"):
                profile = msg.address[6:]
                command = msg.arguments[0]
                if command=="source": 
                    source = msg.arguments[1]
                elif command=="fseq": 
                    fseq = int(msg.arguments[1])
                elif command=="alive":
                    alive = set(msg.arguments[1:])
                elif command=="set":
                    tobj = tuio.TuioDescriptor(msg.source, 
                                               profile, packet.timetag,
                                               source, fseq,
                                               *msg.arguments[1:])
                    desc[tobj.s] = tobj
        # TODO: old bundles rejection based on fseq
        # Update the gestures with the bundle information
        diff = ExtensibleTree()
        for s_id, tobj in desc.items():
            source_ids = self.__idpairs.setdefault(source, {})
            gid = source_ids.get(s_id)
            if gid is None: 
                gid = self.__nextId()
                source_ids[s_id] = gid
            if profile=="2Dcur":
                node = ExtensibleTree()
                node.rel_pos = (tobj.x, tobj.y)
                node.rel_speed = (tobj.X, tobj.Y)
                diff.updated.gestures[gid] = node
            elif profile in ("25Dcur", "3Dcur"):
                node = ExtensibleTree()
                node.rel_pos = (tobj.x, tobj.y, tobj.z)
                node.rel_speed = (tobj.X, tobj.Y, tobj.Z)
                diff.updated.gestures[gid] = node
            elif profile=="2Dblb":
                node = ExtensibleTree()
                node.rel_pos = (tobj.x, tobj.y)
                node.rel_speed = (tobj.X, tobj.Y)
                node.si_angle = (tobj.a, )
                node.rel_size = (tobj.w, tobj.h)
                diff.updated.gestures[gid].boundingbox = node
            elif profile=="25Dblb":
                node = ExtensibleTree()
                node.rel_pos = (tobj.x, tobj.y, tobj.z)
                node.rel_speed = (tobj.X, tobj.Y, tobj.Z)
                node.si_angle = (tobj.a, )
                node.rel_size = (tobj.w, tobj.h)
                diff.updated.gestures[gid].boundingbox = node
            elif profile=="3Dblb":
                node = ExtensibleEvent()
                node.rel_pos = (tobj.x, tobj.y, tobj.z)
                node.rel_speed = (tobj.X, tobj.Y, tobj.Z)
                node.si_angle = (tobj.a, tobj.b, tobj.c)                
                node.rel_size = (tobj.w, tobj.h, tobj.d)
                diff.updated.gestures[gid].boundingbox = node
            elif profile=="2Dobj":
                node = ExtensibleTree()
                node.rel_pos = (tobj.x, tobj.y)
                node.rel_speed = (tobj.X, tobj.Y)
                node.objclass = tobj.i
                node.si_angle = (tobj.a, )
                diff.updated.gestures[gid] = node
            elif profile=="25Dobj":
                node = ExtensibleTree()
                node.rel_pos = (tobj.x, tobj.y, tobj.z)
                node.rel_speed = (tobj.X, tobj.Y, tobj.Z)
                node.objclass = tobj.i
                node.si_angle = (tobj.a, )
                diff.updated.gestures[gid] = node
            elif profile=="3Dobj":
                node = ExtensibleTree()
                node.rel_pos = (tobj.x, tobj.y, tobj.z)
                node.rel_speed = (tobj.X, tobj.Y, tobj.Z)
                node.objclass = tobj.i
                node.si_angle = (tobj.a, tobj.b, tobj.c)
                diff.updated.gestures[gid] = node
        # Remove items that are not alive
        src_profiles = self.__alive.setdefault(source, {})
        alive_old = src_profiles.get(profile, set())
        toRemove = alive_old - alive
        for s_id in toRemove:
            # Check if other profiles has the same session_id still alive
            keep = False
            for p, a in src_profiles.items():
                if p==profile: continue
                elif s_id in a: 
                    keep = True
                    break
            if not keep:
                gid = self.__idpairs.get(source, {}).pop(s_id, None)
                if gid is not None:
                    diff.removed.gestures[gid] = None
        src_profiles[profile] = alive
        additional = {"timetag": timetag}
        self.setState(diff=diff, additional=additional)
        if self._postosc or self._postdata:
            product = {}
            if self._postosc: product["osc"] = packet
            if self._postdata: 
                product["data"] = data if data is not None else packet.encode()
            self._postProduct(product)

    def __nextId(self):
        value = self.__idcount
        self.__idcount += 1
        return value

# ---------------------------------------------------------------------

def TuioSource(url):
    """Return a TuioSource from URL."""
    source = TuioToState()
    if not isinstance(url, URL): url = URL(str(url))
    rt = url.query.data.get("rt")
    source.rt = rt.lower()!="false" if rt is not None else False
    if url.kind in (URL.ABSPATH, URL.RELPATH) \
            or url.scheme=="tuio.file" \
            or (url.scheme=="tuio" and not str(url.site)):
        loop = url.query.data.get("loop")
        speed = url.query.data.get("speed")
        file_ = File(url, File.ReadOnly, uncompress=True)
        player = LogPlayer(file_, parent=source)
        source.subscribeTo(player)
        if speed:
            try: player.setSpeed(float(speed))
            except: print("Cannot set speed:", speed)
        if loop is not None: player.start(loop.lower!="false")
        else: player.start()
    elif url.scheme in ("tuio", "tuio.udp"):
        socket = DataReader(UdpListener(url), parent=source)
        source.subscribeTo(socket)
    elif url.scheme=="tuio.tcp":
        class ClientWaiter(QObject):
            def __init__(self, parent):
                QObject.__init__(self, parent)
                self.socket = None
            def newConnection(self): 
                server = self.sender()
                conn = server.nextPendingConnection()
                if not self.socket:
                    reader = SlipDataReader(conn, parent=source)
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
        server = TcpServer(url.site.host, url.site.port, parent=source)
        server.newConnection.connect(waiter.newConnection)
    else:
        print("WARNING: cannot create TUIO source:", url)
    return source
