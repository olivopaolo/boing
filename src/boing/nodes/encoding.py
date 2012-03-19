# -*- coding: utf-8 -*-
#
# boing/nodes/encoding.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import datetime
import io
import weakref

import boing.net.osc as osc
import boing.net.slip as slip
import boing.net.tuio as tuio
import boing.utils as utils

from boing.core.MappingEconomy import Node, FunctionalNode

# -------------------------------------------------------------------
# TEXT

class TextEncoder(FunctionalNode):
    
    def __init__(self, encoding="utf-8", forward=False, hz=None, parent=None):
        # FIXME: set productoffer
        FunctionalNode.__init__(self, "str", "data", {"data":bytes()}, forward, 
                                hz=hz, parent=parent)
        self.encoding = encoding
  
    def _function(self, paths, values):
        for text in values:
            yield text.encode(self.encoding)


class TextDecoder(FunctionalNode):
    
    def __init__(self, encoding="utf-8", forward=False, hz=None, parent=None):
        # FIXME: set productoffer
        FunctionalNode.__init__(self, "data", "str", {"str":str()}, forward, 
                                hz=hz, parent=parent)
        self.encoding = encoding
        self.errors = "replace"
    
    def _function(self, paths, values):
        for data in values:
            yield data.decode(self.encoding, self.errors)
            
# -------------------------------------------------------------------
# SLIP

class SlipEncoder(FunctionalNode):

    def __init__(self, forward=False, hz=None, parent=None):
        # FIXME: set productoffer
        FunctionalNode.__init__(self, "data", template={"data":bytearray()}, 
                                forward=False, hz=hz, parent=parent)

    def _function(self, paths, values):
        for data in values:
            yield slip.encode(data) if data else bytearray() 


class SlipDecoder(Node):

    def __init__(self, hz=None, parent=None):
        # FIXME: set productoffer
        Node.__init__(self, request="data", hz=hz, parent=parent)
        self._slipbuffer = None
        self._addTag("data", {"data": bytearray()})

    def _consume(self, products, producer):
        if self._tag("data"):
            for p in products:
                encoded = p.get("data")
                if encoded is not None:
                    if encoded:
                        packets, self._slipbuffer = slip.decode(
                            encoded, self._slipbuffer)
                        for packet in packets:
                            self._postProduct({"data": packet})
                    else: 
                        self._postProduct({"data":bytearray()})

# -------------------------------------------------------------------
# OSC

class OscEncoder(FunctionalNode):

    def __init__(self, forward=False, hz=None, parent=None):
        # FIXME: set productoffer
        FunctionalNode.__init__(self, "osc", "data", {"data": bytearray()}, 
                                forward, hz=hz, parent=parent)

    def _function(self, paths, values):
        for packet in values:
            yield packet.encode()


class OscDecoder(FunctionalNode):

    def __init__(self, forward=False, hz=None, parent=None):
        # FIXME: set productoffer
        FunctionalNode.__init__(self, "data", "osc", {"osc": osc.Packet()}, 
                                forward, hz=hz, parent=parent)
    
    def _function(self, paths, values):
        for data in values:
            if data: yield osc.decode(data)


class OscDebug(FunctionalNode):

    def __init__(self, forward=False, hz=None, parent=None):
        #FIXME: set productoffer
        FunctionalNode.__init__(self, "osc", "str", {"str": str()}, 
                                forward, hz=hz, parent=parent)

    def _function(self, paths, values):
        for data in values:
            stream = io.StringIO()
            data.debug(stream)
            yield stream.getvalue()

# -------------------------------------------------------------------
# TUIO

class TuioDecoder(FunctionalNode):
    """Based on the TUIO 1.1 Protocol Specification
    http://www.tuio.org/?specification
    
    It will not work if inside an OSC bundle there is data from more
    than one source or for more than one TUIO profile."""

    def __init__(self, forward=False, hz=None, parent=None):
        template = {"diff": {"added":{"contacts":{}}, 
                             "updated":{"contacts":{}},
                             "removed":{"contacts"}},
                    "timetag": datetime.datetime.now(),
                    "source": str()}
        FunctionalNode.__init__(self, "osc", 
                                lambda paths: ("diff", "timetag", "source"),
                                template, forward, hz=hz, parent=parent)
        """Alive TUIO items."""
        # self.__alive[source][profile] = set of session_ids
        self.__alive = {}
        """Association between the TUIO Session ID and the gesture event ID.
        This is necessary because different TUIO sources may use the same
        Session ID."""
        # self.__idpairs[source][session_id] = event_id
        self.__idpairs = {}
        self.__idcount = 0

    def _function(self, paths, values):
        for packet in values:
            event = self.__handleOsc(packet)
            if event is not None: 
                for item in event: 
                    yield item
  
    def __handleOsc(self, packet):
        timetag = packet.timetag if packet.timetag is not None \
            else datetime.datetime.now()
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
        # Update the contacts with the bundle information
        diff = utils.quickdict()
        for s_id, tobj in desc.items():
            source_ids = self.__idpairs.setdefault(source, {})
            gid = source_ids.get(s_id)
            if gid is None: 
                gid = self.__nextId()
                source_ids[s_id] = gid
            if profile=="2Dcur":
                node = utils.quickdict()
                if tuio.TuioDescriptor.undef_value not in (tobj.x, tobj.y):
                    node.rel_pos = (tobj.x, tobj.y)
                if tuio.TuioDescriptor.undef_value not in (tobj.X, tobj.Y):
                    node.rel_speed = (tobj.X, tobj.Y, 0, 0)
                diff.updated.contacts[gid] = node
            elif profile in ("25Dcur", "3Dcur"):
                node = utils.quickdict()
                node.rel_pos = (tobj.x, tobj.y, tobj.z)
                node.rel_speed = (tobj.X, tobj.Y, tobj.Z, 0)
                diff.updated.contacts[gid] = node
            elif profile=="2Dblb":
                node = utils.quickdict()
                if tuio.TuioDescriptor.undef_value not in (tobj.x, tobj.y):
                    node.rel_pos = (tobj.x, tobj.y)
                if tuio.TuioDescriptor.undef_value not in (tobj.X, tobj.Y):
                    node.rel_speed = (tobj.X, tobj.Y, 0, 0)
                node.si_angle = (tobj.a, )
                node.rel_size = (tobj.w, tobj.h)
                diff.updated.contacts[gid].boundingbox = node
            elif profile=="25Dblb":
                node = utils.quickdict()
                node.rel_pos = (tobj.x, tobj.y, tobj.z)
                node.rel_speed = (tobj.X, tobj.Y, tobj.Z, 0)
                node.si_angle = (tobj.a, )
                node.rel_size = (tobj.w, tobj.h)
                diff.updated.contacts[gid].boundingbox = node
            elif profile=="3Dblb":
                node = ExtensibleEvent()
                node.rel_pos = (tobj.x, tobj.y, tobj.z)
                node.rel_speed = (tobj.X, tobj.Y, tobj.Z, 0)
                node.si_angle = (tobj.a, tobj.b, tobj.c)                
                node.rel_size = (tobj.w, tobj.h, tobj.d)
                diff.updated.contacts[gid].boundingbox = node
            elif profile=="2Dobj":
                node = utils.quickdict()
                if tuio.TuioDescriptor.undef_value not in (tobj.x, tobj.y):
                    node.rel_pos = (tobj.x, tobj.y)
                if tuio.TuioDescriptor.undef_value not in (tobj.X, tobj.Y):
                    node.rel_speed = (tobj.X, tobj.Y, 0, 0)
                node.objclass = tobj.i
                node.si_angle = (tobj.a, )
                diff.updated.contacts[gid] = node
            elif profile=="25Dobj":
                node = utils.quickdict()
                node.rel_pos = (tobj.x, tobj.y, tobj.z)
                node.rel_speed = (tobj.X, tobj.Y, tobj.Z, 0)
                node.objclass = tobj.i
                node.si_angle = (tobj.a, )
                diff.updated.contacts[gid] = node
            elif profile=="3Dobj":
                node = utils.quickdict()
                node.rel_pos = (tobj.x, tobj.y, tobj.z)
                node.rel_speed = (tobj.X, tobj.Y, tobj.Z, 0)
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
        return (diff, timetag, source) if diff else None

    def __nextId(self):
        value = self.__idcount
        self.__idcount += 1
        return str(value)

# -------------------------------------------------------------------

class TuioEncoder(Node):
    """Convert contact events into OSC/TUIO packets."""
    def __init__(self, request="diff.*.contacts|source", hz=None, parent=None):
        Node.__init__(self, request=request, parent=parent)
        # self._tuiostate[observable-ref][source][profile] = [fseq, {s_id: TuioDescriptor}]
        self._tuiostate = {}
    
    def _checkRef(self):
        Node._checkRef(self)
        self._tuiostate = dict(((k,v) for k,v in self._tuiostate.items() \
                                    if k() is not None))

    def _removeObservable(self, observable):
        Node._removeObservable(self, observable)
        for ref in self._tuiostate.keys():
            if ref() is observable:
                del self._tuiostate[ref] ; break

    def __sourcetuiostate(self, observable, src):
        """Return the record associated to observable."""
        for ref, sources in self._tuiostate.items():
            if ref() is observable: 
                rvalue = sources.setdefault(src, utils.quickdict())
                break
        else:
            rvalue = utils.quickdict()
            self._tuiostate[weakref.ref(observable)] = {src:rvalue}
        return rvalue

    def _consume(self, products, producer):
        for product in products:
            if "diff" in product:
                # Set of s_id that have been updated.  
                # setters[<profile>] = {s_id1, s_id2, ..., s_idn}
                setters = {}
                # Set of profiles for which a s_id have been removed
                removed = set() 
                diff = product["diff"]
                src = product.get("source", str(producer))
                sourcetuiostate = self.__sourcetuiostate(producer, src)
                toupdate = None
                if "added" in diff: toupdate = diff.added.contacts
                if "updated" in diff:
                    if toupdate is None: 
                        toupdate = diff.updated.contacts
                    else:
                        utils.deepupdate(toupdate, diff.updated.contacts)
                if toupdate is not None:
                    for gid, gdiff in toupdate.items():
                        # Determine the TUIO profiles for the gesture event
                        profiles = set()
                        for profile, profilestate in sourcetuiostate.items():
                            if gid in profilestate[1]: profiles.add(profile)
                        if not profiles:
                            if "rel_pos" in gdiff:
                                if "objclass" in gdiff: 
                                    if len(gdiff.rel_pos)==2: 
                                        profiles.add("2Dobj")
                                    elif len(gdiff.rel_pos)==3: 
                                        profiles.add("3Dobj")
                                elif len(gdiff.rel_pos)==2: 
                                    profiles.add("2Dcur")
                                elif len(gdiff.rel_pos)==3: 
                                    profiles.add("3Dcur")
                            if "boundingbox" in gdiff: 
                                if "rel_pos" in gdiff.boundingbox:
                                    if len(gdiff.boundingbox.rel_pos)==2: 
                                        profiles.add("2Dblb")
                                    elif len(gdiff.boundingbox.rel_pos)==3: 
                                        profiles.add("3Dblb")
                                elif "rel_pos" in gdiff:
                                    if len(gdiff.rel_pos)==2: 
                                        profiles.add("2Dblb")
                                    elif len(gdiff.rel_pos)==3: 
                                        profiles.add("3Dblb")
                        elif len(profiles)==1 and "boundingbox" in gdiff:
                            if "rel_pos" in gdiff.boundingbox:
                                if len(gdiff.boundingbox.rel_pos)==2: 
                                    profiles.add("2Dblb")
                                elif len(gdiff.boundingbox.rel_pos)==3: 
                                    profiles.add("3Dblb")
                            elif "rel_pos" in gdiff:
                                if len(gdiff.rel_pos)==2: profiles.add("2Dblb")
                                elif len(gdiff.rel_pos)==3: profiles.add("3Dblb")
                        # Create set descriptors for each updated profile
                        for profile in profiles:
                            update = False
                            profilestate = sourcetuiostate.setdefault(
                                profile, [0, {}])
                            if gid in profilestate[1]: 
                                prev = profilestate[1][gid]
                            else:
                                len_ = len(tuio.TuioDescriptor.profiles[profile])
                                prev = tuio.TuioDescriptor(
                                    None, profile, None, None, None,
                                    *([tuio.TuioDescriptor.undef_value]*len_))
                                prev.s = int(gid)
                                profilestate[1][gid] = prev
                                update = True
                            if profile=="2Dcur":
                                if "rel_pos" in gdiff:
                                    prev.x, prev.y = gdiff.rel_pos[:2]
                                    update = True
                                if "rel_speed" in gdiff:
                                    prev.X, prev.Y = gdiff.rel_speed[:2]
                                    update = True
                            elif profile in ("25Dcurr", "3Dcur"):
                                if "rel_pos" in gdiff:
                                    prev.x, prev.y, prev.z= gdiff.rel_pos[:3]
                                    update = True
                                if "rel_speed" in gdiff:
                                    prev.X, prev.Y, prev.Z = gdiff.rel_speed[:3]
                                    update = True
                            elif profile=="2Dobj":
                                if "rel_pos" in gdiff: 
                                    prev.x, prev.y = gdiff.rel_pos[:2]
                                    update = True
                                if "rel_speed" in gdiff:
                                    prev.X, prev.Y = gdiff.rel_speed[:2]
                                    update = True
                                if "si_angle" in gdiff: 
                                    prev.a = gdiff.si_angle[0]
                                    update = True
                                if "objclass" in gdiff:
                                    prev.i = gdiff.objclass
                                    update = True
                            elif profile=="25Dobj":
                                if "rel_pos" in gdiff:
                                    prev.x, prev.y, prev.z= gdiff.rel_pos[:3]
                                    update = True
                                if "rel_speed" in gdiff:
                                    prev.X, prev.Y, prev.Z = gdiff.rel_speed[:3]
                                    update = True
                                if "si_angle" in gdiff: 
                                    prev.a = gdiff.si_angle[0]
                                    update = True
                                if "objclass" in gdiff:
                                    prev.i = gdiff.objclass
                                    update = True
                            elif profile=="3Dobj":
                                if "rel_pos" in gdiff:
                                    prev.x, prev.y, prev.z= gdiff.rel_pos[:3]
                                    update = True
                                if "rel_speed" in gdiff:
                                    prev.X, prev.Y, prev.Z = gdiff.rel_speed[:3]
                                    update = True
                                if "si_angle" in gdiff: 
                                    prev.a, prev.b, prev.c = gdiff.si_angle[:3]
                                    update = True
                                if "objclass" in gdiff:
                                    prev.i = gdiff.objclass
                                    update = True
                            elif profile=="2Dblb":
                                if "boundingbox" in gdiff:
                                    bb = gdiff.boundingbox
                                    if "rel_pos" in bb: 
                                        prev.x, prev.y = bb.rel_pos[:2]
                                        update = True
                                    if "rel_speed" in bb:
                                        prev.X, prev.Y = bb.rel_speed[:2]
                                        update = True
                                    if "si_angle" in bb:
                                        prev.a = bb.si_angle[0]
                                        update = True
                                    if "rel_size" in bb:
                                        prev.w, prev.h = bb.rel_size[:2]
                                        update = True
                            elif profile=="25Dblb":
                                if "boundingbox" in gdiff:
                                    bb = gdiff.boundingbox
                                    if "rel_pos" in bb: 
                                        prev.x, prev.y, prev.z = bb.rel_pos[:3]
                                        update = True
                                    if "rel_speed" in bb:
                                        prev.X, prev.Y, prev.Z = bb.rel_speed[:3]
                                        update = True
                                    if "si_angle" in bb:
                                        prev.a = bb.si_angle[0]
                                        update = True
                                    if "rel_size" in bb:
                                        prev.w, prev.h = bb.rel_size[:2]
                                        update = True
                            elif profile=="3Dblb":
                                if "boundingbox" in gdiff:
                                    bb = gdiff.boundingbox
                                    if "rel_pos" in bb: 
                                        prev.x, prev.y, prev.z = bb.rel_pos[:3]
                                        update = True
                                    if "rel_speed" in bb:
                                        prev.X, prev.Y, prev.Z = bb.rel_speed[:3]
                                        update = True
                                    if "si_angle" in bb:
                                        prev.a, prev.b, prev.c = bb.si_angle[:3]
                                        update = True
                                    if "rel_size" in bb:
                                        prev.w, prev.h, prev.d = bb.rel_size[:3]
                                        update = True
                            if update: setters.setdefault(profile, set()).add(gid)
                if "removed" in diff:
                    for gid in diff.removed.contacts.keys():
                        for profile, profilestate in sourcetuiostate.items():
                            if gid in profilestate[1]:
                                del profilestate[1][gid]
                                removed.add(profile)
                                if profile in setters:
                                    setters[profile].discard(gid)
                # Create an OSC bundle 
                packets = []
                for profile in (set(setters.keys()) | removed):
                    profilestate = sourcetuiostate[profile]
                    sourcemsg = osc.Message("/tuio/%s"%profile, 
                                            "ss", "source", 
                                            src)
                    alive = list(int(gid) for gid in profilestate[1].keys())
                    alivemsg = osc.Message("/tuio/%s"%profile, 
                                           "s"+"i"*len(alive), "alive", 
                                           *alive)
                    msgs = [sourcemsg, alivemsg]
                    profilesetters = setters.get(profile)
                    if profilesetters is not None:
                        setmsgs = []
                        for s_id in profilesetters:
                            desc = profilestate[1][s_id]
                            args = []
                            for name in tuio.TuioDescriptor.profiles[profile]:
                                args.append(getattr(desc, name))
                            setmsgs.append(osc.Message("/tuio/%s"%profile,
                                                       None, "set", 
                                                       *args))
                        msgs.extend(setmsgs)
                    msgs.append(osc.Message("/tuio/%s"%profile, 
                                            "si", "fseq", 
                                            profilestate[0]))
                    profilestate[0] += 1
                    forward = utils.quickdict()
                    forward.osc = osc.Bundle(product.get("timetag"), msgs)
                    self._postProduct(forward)
