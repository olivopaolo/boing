# -*- coding: utf-8 -*-
#
# boing/nodes/encoding.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import datetime
import io
import weakref

from PyQt4 import QtCore

from boing import Offer, QRequest, Functor
from boing.nodes.logger import FilePlayer
from boing.net import json, osc, slip, tuio, Decoder
from boing.utils import assertIsInstance, deepupdate, quickdict

# -------------------------------------------------------------------
# TEXT

class TextEncoder(Functor):

    def __init__(self, encoding="utf-8", blender=Functor.MERGECOPY, parent=None):
        super().__init__(QRequest("str"), Offer(quickdict(data=bytearray())),
                         blender, parent=parent)
        self.encoding = assertIsInstance(encoding, str)

    def _process(self, sequence, producer):
        for operands in sequence:
            for name, value in operands:
                yield (("data", value.encode(self.encoding)), )


class TextDecoder(Functor):

    def __init__(self, encoding="utf-8", blender=Functor.MERGECOPY, parent=None):
        super().__init__(QRequest("data"), Offer(quickdict(str=str())),
                         blender, parent=parent)
        self.encoding = assertIsInstance(encoding, str)
        self.errors = "replace"

    def _process(self, sequence, producer):
        for operands in sequence:
            for name, value in operands:
                yield (("str", value.decode(self.encoding, self.errors)), )

# -------------------------------------------------------------------
# SLIP

class SlipEncoder(Functor):

    def __init__(self, blender=Functor.MERGECOPY, parent=None):
        super().__init__(QRequest("data"), Offer(quickdict(data=bytearray())),
                         blender, parent=parent)

    def _process(self, sequence, producer):
        for operands in sequence:
            for name, value in operands:
                data = slip.encode(value) if value else bytearray()
                yield (("data", data), )


class SlipDecoder(Functor):
    def __init__(self, parent=None):
        # It is forced to be use a RESULTONLY blender because for each
        # received product, it may produce multiple products.
        super().__init__(QRequest("data"), Offer(quickdict(data=bytearray())),
                         Functor.RESULTONLY, parent=parent)
        self._slipbuffer = None

    def _process(self, sequence, producer):
        for operands in sequence:
            for name, value in operands:
                if not value: yield (("data", bytearray()), )
                else:
                    packets, self._slipbuffer = \
                        slip.decode(value, self._slipbuffer)
                    for packet in packets:
                        yield (("data", packet), )

# -------------------------------------------------------------------
# JSON

class JsonEncoder(Functor):

    def __init__(self, wrap=False,
                 request=QRequest.ANY, blender=Functor.MERGECOPY, parent=None):
        super().__init__(request, Offer(quickdict(str=str())),
                         blender, parent=parent)
        self.wrap = assertIsInstance(wrap, bool)

    def _process(self, sequence, producer):
        if self.wrap:
            products = tuple(map(quickdict, sequence))
            yield (("str", json.encode(quickdict(timetag=datetime.datetime.now(),
                                                 products=products))), )
        else:
            for operands in sequence:
                yield (("str", json.encode(quickdict(operands))),)


class JsonDecoder(Functor):

    def __init__(self, blender=Functor.MERGECOPY, parent=None):
        super().__init__(QRequest("str"), Offer(Offer.UndefinedProduct()),
                         blender, parent=parent)

    def _process(self, sequence, producer):
        for operands in sequence:
            for name, value in operands:
                if value:
                    product = json.decode(value)
                    yield product.items() if hasattr(product, "items") \
                        else (("array", product), )

# -------------------------------------------------------------------
# OSC

class OscEncoder(Functor):

    def __init__(self, wrap=False, rt=False,
                 blender=Functor.RESULTONLY, parent=None):
        super().__init__(QRequest("osc"), Offer(quickdict(data=bytearray())),
                         blender, parent=parent)
        self.wrap = assertIsInstance(wrap, bool)
        self.rt = assertIsInstance(rt, bool)

    def _process(self, sequence, producer):
        now = datetime.datetime.now()
        for operands in sequence:
            for name, value in operands:
                bundle = osc.Bundle(now if not self.rt else value.timetag,
                                    value.elements)
                packet = osc.EncodedPacket(bundle.encode())
                if self.wrap: packet = osc.Bundle(now, (packet,))
                yield (('data', packet.encode()), )


class OscDecoder(Functor):

    def __init__(self, rt=False, blender=Functor.MERGECOPY, parent=None):
        super().__init__(QRequest("data"),
                         Offer(quickdict(osc=osc.Packet(),
                                       timetag=datetime.datetime.now())),
                         blender, parent=parent)
        self._receipttime = assertIsInstance(rt, bool)

    def _process(self, sequence, producer):
        for operands in sequence:
            for name, value in operands:
                if value:
                    packet = osc.decode(value)
                    yield (('osc', packet),
                           ('timetag', packet.timetag if not self._receipttime \
                                else datetime.datetime.now()))

class OscDebug(Functor):

    def __init__(self, blender=Functor.MERGECOPY, parent=None):
        super().__init__(QRequest("osc"), Offer(quickdict(str=str())),
                         blender, parent=parent)

    def _process(self, sequence, producer):
        stream = io.StringIO()
        for operands in sequence:
            for name, value in operands:
                value.debug(stream)
        yield (('str', stream.getvalue()), )


class OscLogPlayer(FilePlayer):

    def __init__(self, filename, **kwargs):
        super().__init__(filename,
                         OscLogPlayer._Decoder(),
                         OscLogPlayer._Sender(),
                         offer=Offer(quickdict(osc=osc.Packet(),
                                             timetag=datetime.datetime.now())),
                         **kwargs)

    class _Decoder(Decoder):
        def __init__(self):
            self.unslip = slip.Decoder()

        def decode(self, encoded):
            unslipped = self.unslip.decode(encoded)
            return tuple(osc.decode(obj) for obj in unslipped)

        def reset(self): self.unslip.reset()

    class _Sender(FilePlayer.Sender):
        def send(self, player, obj):
            for packet in obj.elements:
                packet.timetag = player._date if player._date is not None \
                    else datetime.datetime.now()
                player.postProduct(quickdict(osc=packet, timetag=packet.timetag))

# -------------------------------------------------------------------
# TUIO

class TuioDecoder(Functor):
    """Based on the TUIO 1.1 Protocol Specification
    http://www.tuio.org/?specification

    It will not work if inside an OSC bundle there is data from more
    than one source or for more than one TUIO profile."""

    def __init__(self, blender=Functor.MERGECOPY, parent=None):
        super().__init__(QRequest("osc"), Offer(TuioDecoder.getTemplate()),
                         blender, parent=parent)
        """Alive TUIO items."""
        # self.__alive[source][profile] = set of session_ids
        self.__alive = {}
        """Association between the TUIO Session ID and the gesture event ID.
        This is necessary because different TUIO sources may use the same
        Session ID."""
        # self.__idpairs[source][session_id] = event_id
        self.__idpairs = {}
        self.__idcount = 0

    def _process(self, sequence, producer):
        for operands in sequence:
            for name, value in operands:
                yield tuple(self.__handleOsc(value))

    def __handleOsc(self, packet):
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
        for s_id, tobj in desc.items():
            source_ids = self.__idpairs.setdefault(source, {})
            gid = source_ids.get(s_id)
            if gid is None:
                gid = self.__nextId()
                source_ids[s_id] = gid
            if profile=="2Dcur":
                node = quickdict()
                if tuio.TuioDescriptor.undef_value not in [tobj.x, tobj.y]:
                    node.rel_pos = [tobj.x, tobj.y]
                if tuio.TuioDescriptor.undef_value not in [tobj.X, tobj.Y]:
                    node.rel_speed = [tobj.X, tobj.Y, 0, 0]
                yield "diff.updated.contacts.%s"%gid, node
            elif profile in ("25Dcur", "3Dcur"):
                node = quickdict()
                node.rel_pos = [tobj.x, tobj.y, tobj.z]
                node.rel_speed = [tobj.X, tobj.Y, tobj.Z, 0]
                yield "diff.updated.contacts.%s"%gid, node
            elif profile=="2Dblb":
                node = quickdict()
                if tuio.TuioDescriptor.undef_value not in [tobj.x, tobj.y]:
                    node.rel_pos = [tobj.x, tobj.y]
                if tuio.TuioDescriptor.undef_value not in [tobj.X, tobj.Y]:
                    node.rel_speed = [tobj.X, tobj.Y, 0, 0]
                node.si_angle = [tobj.a, ]
                node.rel_size = [tobj.w, tobj.h]
                yield "diff.updated.contacts.%s.boundingbox"%gid, node
            elif profile=="25Dblb":
                node = quickdict()
                node.rel_pos = [tobj.x, tobj.y, tobj.z]
                node.rel_speed = [tobj.X, tobj.Y, tobj.Z, 0]
                node.si_angle = [tobj.a, ]
                node.rel_size = [tobj.w, tobj.h]
                yield "diff.updated.contacts.%s.boundingbox"%gid, node
            elif profile=="3Dblb":
                node = quickdict()
                node.rel_pos = [tobj.x, tobj.y, tobj.z]
                node.rel_speed = [tobj.X, tobj.Y, tobj.Z, 0]
                node.si_angle = [tobj.a, tobj.b, tobj.c]
                node.rel_size = [tobj.w, tobj.h, tobj.d]
                yield "diff.updated.contacts.%s.boundingbox"%gid, node
            elif profile=="2Dobj":
                node = quickdict()
                if tuio.TuioDescriptor.undef_value not in [tobj.x, tobj.y]:
                    node.rel_pos = [tobj.x, tobj.y]
                if tuio.TuioDescriptor.undef_value not in [tobj.X, tobj.Y]:
                    node.rel_speed = [tobj.X, tobj.Y, 0, 0]
                node.objclass = tobj.i
                node.si_angle = [tobj.a, ]
                yield "diff.updated.contacts.%s"%gid, node
            elif profile=="25Dobj":
                node = quickdict()
                node.rel_pos = [tobj.x, tobj.y, tobj.z]
                node.rel_speed = [tobj.X, tobj.Y, tobj.Z, 0]
                node.objclass = tobj.i
                node.si_angle = [tobj.a, ]
                yield "diff.updated.contacts.%s"%gid, node
            elif profile=="3Dobj":
                node = quickdict()
                node.rel_pos = [tobj.x, tobj.y, tobj.z]
                node.rel_speed = [tobj.X, tobj.Y, tobj.Z, 0]
                node.objclass = tobj.i
                node.si_angle = [tobj.a, tobj.b, tobj.c]
                yield "diff.updated.contacts.%s"%gid, node
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
                    yield "diff.removed.contacts.%s"%gid, None
        src_profiles[profile] = alive
        yield "source", source

    def __nextId(self):
        value = self.__idcount
        self.__idcount += 1
        return str(value)

    @staticmethod
    def getTemplate():
        template = quickdict()
        contact = template.diff.added.contacts[0]
        contact.rel_pos = tuple()
        contact.rel_speed = tuple()
        contact.rel_accel = tuple()
        contact.si_angle = tuple()
        contact.objclass = tuple()
        contact.boundingbox.rel_pos = tuple()
        contact.boundingbox.rel_speed = tuple()
        contact.boundingbox.si_angle = tuple()
        contact.boundingbox.rel_size = tuple()
        template.diff.updated.contacts[0] = contact
        template.diff.removed.contact[0] = None
        template.source = str()
        return template


class TuioEncoder(Functor):
    """Convert contact events into OSC/TUIO packets."""
    def __init__(self, request=QRequest("diff.*.contacts|source|timetag"), 
                 blender=Functor.RESULTONLY, hz=None, parent=None):
        super().__init__(request, Offer(quickdict(osc=osc.Packet)), blender,
                         hz=hz, parent=parent)
        # self._tuiostate[observable-ref][source][profile] = [fseq, {s_id: TuioDescriptor}]
        self._tuiostate = {}
        self.observableRemoved.connect(self.__removeRecord)

    
    def _checkRefs(self):
        super()._checkRefs()
        self._tuiostate = dict(((k,v) for k,v in self._tuiostate.items() \
                                    if k() is not None))

    def __removeRecord(self, observable):
        for ref in self._tuiostate.keys():
            if ref() is observable:
                del self._tuiostate[ref] ; break

    def __sourcetuiostate(self, observable, src):
        """Return the record associated to observable."""
        for ref, sources in self._tuiostate.items():
            if ref() is observable: 
                rvalue = sources.setdefault(src, quickdict())
                break
        else:
            rvalue = quickdict()
            self._tuiostate[weakref.ref(observable)] = {src:rvalue}
        return rvalue

    def _consume(self, products, producer):
        for product in products:
            if "diff" in product: self._encodeEvent(product, producer)
                    

    def _encodeEvent(self, event, producer):
        # Set of s_id that have been updated.  
        # setters[<profile>] = {s_id1, s_id2, ..., s_idn}
        setters = {}
        # Set of profiles for which a s_id have been removed
        removed = set() 
        diff = event["diff"]
        src = event.get("source", str(producer))
        sourcetuiostate = self.__sourcetuiostate(producer, src)
        toupdate = None
        if "added" in diff: toupdate = diff.added.contacts
        if "updated" in diff:
            if toupdate is None: 
                toupdate = diff.updated.contacts
            else:
                deepupdate(toupdate, diff.updated.contacts)
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
                    else:
                        for other in profiles: break
                        if other.startswith("2D"): profiles.add("2Dblb")
                        elif other.startswith("3D"): profiles.add("3Dblb")
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
            sourcemsg = osc.Message("/tuio/%s"%profile, "ss", "source", src)
            alive = list(int(gid) for gid in profilestate[1].keys())
            alivemsg = osc.Message("/tuio/%s"%profile, 
                                   "s"+"i"*len(alive), "alive", *alive)
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
                                               None, "set", *args))
                msgs.extend(setmsgs)
            msgs.append(osc.Message("/tuio/%s"%profile, "si", "fseq", 
                                    profilestate[0]))
            profilestate[0] += 1
            forward = quickdict()
            forward.osc = osc.Bundle(event.get("timetag"), msgs)
            self.postProduct(forward)
