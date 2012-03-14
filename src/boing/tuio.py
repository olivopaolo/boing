# -*- coding: utf-8 -*-
#
# boing/tuio.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import weakref
import datetime

import boing.osc as osc
import boing.utils as utils
from boing.eventloop.MappingEconomy import Node

class TuioDescriptor(object):

    """Based on the TUIO 1.1 Protocol Specification
       http://www.tuio.org/?specification"""
    
    profiles = {
        "2Dobj":("s","i","x","y","a","X","Y","A","m","r"),
        "2Dcur":("s","x","y","X","Y","m"),
        "2Dblb":("s","x","y","a","w","h","f","X","Y","A","m","r"),
        "25Dobj":("s","i","x","y","z","a","X","Y","Z","A","m","r"),
        "25Dcur":("s","x","y","z","X","Y","Z","m"),
        "25Dblb":("s","x","y","z","a","w","h","f","X","Y","Z","A","m","r"),
        "3Dobj":("s","i","x","y","z","a","b","c","X","Y","Z","A","B","C","m","r"),
        "3Dcur":("s","x","y","z","X","Y","Z","m"),
        "3Dblb":("s","x","y","z","a","b","c","w","h","d","v","X","Y","Z","A","B","C","m","r"),
        }

    undef_value = -1.0

    def __init__(self, client,
                 profile, timetag, source, fseq,
                 *args):
        self.client = client
        self.profile = profile
        self.timetag = timetag
        self.source = source
        self.fseq = fseq
        names = TuioDescriptor.profiles[profile]
        if len(names)!=len(args):
            raise IndexError("""expecting "%s" for a %s"""%(names,profile))
        for name, arg in zip(names, args):
            self.__dict__[name] = arg

    def __str__(self):
        strings = [self.profile]
        for name in TuioDescriptor.profiles[self.profile]:
            strings.append("%s=%s"%(name,self.__dict__[name]))
        return " ".join(strings)

# -------------------------------------------------------------------

class TuioDecoder(Node):
    """Based on the TUIO 1.1 Protocol Specification
    http://www.tuio.org/?specification
    
    It will not work if inside an OSC bundle there is data from more
    than one source or for more than one TUIO profile."""

    def __init__(self, rt=False, parent=None):
        Node.__init__(self, request="osc", parent=parent)
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
        template = {"diff":{"added":{"contacts":{}}, 
                            "updated":{"contacts":{}},
                            "removed":{"contacts"}}}
        self._addTag("diff", template, update=False)

    def _consume(self, products, producer):
        for p in products:
            if "osc" in p and self._tag("diff"): self.__handleOsc(p["osc"])

    def __handleOsc(self, packet):
        timetag = datetime.datetime.now() \
            if self.rt or packet.timetag is None else packet.timetag
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
        diff = utils.quickdict()
        for s_id, tobj in desc.items():
            source_ids = self.__idpairs.setdefault(source, {})
            gid = source_ids.get(s_id)
            if gid is None: 
                gid = self.__nextId()
                source_ids[s_id] = gid
            if profile=="2Dcur":
                node = utils.quickdict()
                if TuioDescriptor.undef_value not in (tobj.x, tobj.y):
                    node.rel_pos = (tobj.x, tobj.y)
                if TuioDescriptor.undef_value not in (tobj.X, tobj.Y):
                    node.rel_speed = (tobj.X, tobj.Y, 0, 0)
                diff.updated.contacts[gid] = node
            elif profile in ("25Dcur", "3Dcur"):
                node = utils.quickdict()
                node.rel_pos = (tobj.x, tobj.y, tobj.z)
                node.rel_speed = (tobj.X, tobj.Y, tobj.Z, 0)
                diff.updated.contacts[gid] = node
            elif profile=="2Dblb":
                node = utils.quickdict()
                if TuioDescriptor.undef_value not in (tobj.x, tobj.y):
                    node.rel_pos = (tobj.x, tobj.y)
                if TuioDescriptor.undef_value not in (tobj.X, tobj.Y):
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
                if TuioDescriptor.undef_value not in (tobj.x, tobj.y):
                    node.rel_pos = (tobj.x, tobj.y)
                if TuioDescriptor.undef_value not in (tobj.X, tobj.Y):
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
        product = {"diff":diff, "timetag": timetag, "source":source}
        if diff: self._postProduct(product)

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
                                len_ = len(TuioDescriptor.profiles[profile])
                                prev = TuioDescriptor(
                                    None, profile, None, None, None,
                                    *([TuioDescriptor.undef_value]*len_))
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
                            for name in TuioDescriptor.profiles[profile]:
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
