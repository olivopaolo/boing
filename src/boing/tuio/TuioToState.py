# -*- coding: utf-8 -*-
#
# boing/tuio/TuioToState.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from datetime import datetime

from PyQt4 import QtCore 

from boing import osc
from boing.eventloop.StateMachine import StateNode
from boing.tuio import TuioDescriptor
from boing.utils import quickdict

class TuioToState(StateNode):
    """Based on the TUIO 1.1 Protocol Specification
    http://www.tuio.org/?specification
    
    It will not work if inside an OSC bundle there is data from more
    than one source or for more than one TUIO profile."""

    def __init__(self, rt=False, parent=None):
        StateNode.__init__(self, request="osc", parent=parent)
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
        self.rt = rt

    def _consume(self, products, producer):
        for p in products:
            packet = p.get("osc")
            if isinstance(packet, osc.Bundle): self.__handleOsc(packet)

    def __handleOsc(self, packet):
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
                    tobj = TuioDescriptor(msg.source, 
                                          profile, packet.timetag,
                                          source, fseq,
                                          *msg.arguments[1:])
                    desc[tobj.s] = tobj
        # TODO: old bundles rejection based on fseq
        # Update the contacts with the bundle information
        diff = quickdict()
        for s_id, tobj in desc.items():
            source_ids = self.__idpairs.setdefault(source, {})
            gid = source_ids.get(s_id)
            if gid is None: 
                gid = self.__nextId()
                source_ids[s_id] = gid
            if profile=="2Dcur":
                node = quickdict()
                if TuioDescriptor.undef_value not in (tobj.x, tobj.y):
                    node.rel_pos = (tobj.x, tobj.y)
                if TuioDescriptor.undef_value not in (tobj.X, tobj.Y):
                    node.rel_speed = (tobj.X, tobj.Y)
                diff.updated.contacts[gid] = node
            elif profile in ("25Dcur", "3Dcur"):
                node = quickdict()
                node.rel_pos = (tobj.x, tobj.y, tobj.z)
                node.rel_speed = (tobj.X, tobj.Y, tobj.Z)
                diff.updated.contacts[gid] = node
            elif profile=="2Dblb":
                node = quickdict()
                if TuioDescriptor.undef_value not in (tobj.x, tobj.y):
                    node.rel_pos = (tobj.x, tobj.y)
                if TuioDescriptor.undef_value not in (tobj.X, tobj.Y):
                    node.rel_speed = (tobj.X, tobj.Y)
                node.si_angle = (tobj.a, )
                node.rel_size = (tobj.w, tobj.h)
                diff.updated.contacts[gid].boundingbox = node
            elif profile=="25Dblb":
                node = quickdict()
                node.rel_pos = (tobj.x, tobj.y, tobj.z)
                node.rel_speed = (tobj.X, tobj.Y, tobj.Z)
                node.si_angle = (tobj.a, )
                node.rel_size = (tobj.w, tobj.h)
                diff.updated.contacts[gid].boundingbox = node
            elif profile=="3Dblb":
                node = ExtensibleEvent()
                node.rel_pos = (tobj.x, tobj.y, tobj.z)
                node.rel_speed = (tobj.X, tobj.Y, tobj.Z)
                node.si_angle = (tobj.a, tobj.b, tobj.c)                
                node.rel_size = (tobj.w, tobj.h, tobj.d)
                diff.updated.contacts[gid].boundingbox = node
            elif profile=="2Dobj":
                node = quickdict()
                if TuioDescriptor.undef_value not in (tobj.x, tobj.y):
                    node.rel_pos = (tobj.x, tobj.y)
                if TuioDescriptor.undef_value not in (tobj.X, tobj.Y):
                    node.rel_speed = (tobj.X, tobj.Y)
                node.objclass = tobj.i
                node.si_angle = (tobj.a, )
                diff.updated.contacts[gid] = node
            elif profile=="25Dobj":
                node = quickdict()
                node.rel_pos = (tobj.x, tobj.y, tobj.z)
                node.rel_speed = (tobj.X, tobj.Y, tobj.Z)
                node.objclass = tobj.i
                node.si_angle = (tobj.a, )
                diff.updated.contacts[gid] = node
            elif profile=="3Dobj":
                node = quickdict()
                node.rel_pos = (tobj.x, tobj.y, tobj.z)
                node.rel_speed = (tobj.X, tobj.Y, tobj.Z)
                node.objclass = tobj.i
                node.si_angle = (tobj.a, tobj.b, tobj.c)
                diff.updated.contacts[gid] = node
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
                    diff.removed.contacts[gid] = None
        src_profiles[profile] = alive
        self.applyDiff(diff, {"timetag": timetag})

    def __nextId(self):
        value = self.__idcount
        self.__idcount += 1
        return value

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
        class ClientWaiter(QtCore.QObject):
            def __init__(self, parent):
                QtCore.QObject.__init__(self, parent)
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
        source = None
    return source
'''
