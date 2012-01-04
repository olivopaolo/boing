# -*- coding: utf-8 -*-
#
# boing/tuio/StateToTuio.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import datetime
import weakref

from boing import osc
from boing.eventloop.MappingEconomy import MappingProducer, parseRequests
from boing.eventloop.OnDemandProduction import OnDemandProducer, SelectiveConsumer
from boing.osc.LogFile import LogFile
from boing.slip.SlipDataIO import SlipDataWriter
from boing.tcp.TcpSocket import TcpConnection
from boing.tuio import TuioDescriptor
from boing.udp.UdpSocket import UdpSender
from boing.url import URL
from boing.utils.DataIO import DataWriter
from boing.utils.ExtensibleTree import ExtensibleTree
from boing.utils.File import File

class StateToTuio(MappingProducer, SelectiveConsumer):
    """Convert gesture events into OSC/TUIO packets."""
    def __init__(self,
                 requests={("diff", ".*", "gestures"), "timetag", "osc", "data"},
                 hz=None, parent=None):
        MappingProducer.__init__(self, productoffer={"osc", "data"},
                                 parent=parent)
        SelectiveConsumer.__init__(self, requests, hz)
        # self._tuiostate[observable-ref][profile] = [fseq, {s_id: TuioDescriptor}]
        self._tuiostate = {}

    def __del__(self):
        MappingProducer.__del__(self)        
        SelectiveConsumer.__del__(self)
    
    def _removeObservable(self, observable):
        MappingProducer._removeObservable(self, observable)
        for ref in self._tuiostate.keys():
            if ref() is observable:
                del self._tuiostate[ref] ; break

    def _checkRef(self):
        MappingProducer._checkRef(self)
        SelectiveConsumer._checkRef(self)
        self._tuiostate = dict(((k,v) for k,v in self._tuiostate.items() \
                                    if k() is not None))

    def subscribeTo(self, observable, **kwargs):
        """Accepts argument 'requests' also."""
        rvalue = False
        for key in kwargs.keys():
            if key!="requests":
                raise TypeError(
                    "subscribeTo() got an unexpected keyword argument '%s'"%key)
        if isinstance(observable, OnDemandProducer):
            if "requests" in kwargs:
                rvalue = observable.addObserver(self, requests=kwargs["requests"])
            elif "osc" in self._requests:
                # Optimize OSC forwarding, excluding gesture event translation
                offer = observable.productOffer()
                if isinstance(offer, collections.Container) and "osc" in offer:
                    requests = {"osc", "data"} if "data" in offer else "osc"
                    rvalue = observable.addObserver(self, requests=requests)
                elif offer=="osc":
                    rvalue = observable.addObserver(self, requests=offer)
                else:
                    rvalue = observable.addObserver(self, requests=self._requests)
            else:
                rvalue = observable.addObserver(self, requests=self._requests)
        else:
            rvalue = Consumer.subscribeTo(self, observable) 
        return rvalue

    def _consume(self, products, producer):
        sourcetuiostate = None
        for ref, state in self._tuiostate.items():
            if ref() is producer: sourcetuiostate = state ; break
        else:
            sourcetuiostate = dict()
            self._tuiostate[weakref.ref(producer)] = sourcetuiostate
        for product in products:
            if isinstance(product, collections.Mapping):
                if "osc" in product:
                    if "data" in product: 
                        # Directly forward the product 
                        self._postProduct(product)
                    else:
                        # Create a new product since data is missing
                        forward = ExtensibleTree()
                        forward.osc = product["osc"]
                        forward.data = product["osc"].encode()
                        self._postProduct(forward)
                elif "diff" in product:
                    # Set of s_id that have been updated.  
                    # setters[<profile>] = {s_id1, s_id2, ..., s_idn}
                    setters = {}
                    # Set of profiles for which a s_id have been removed
                    removed = set() 
                    diff = product["diff"]                    
                    update_tree = None
                    if "added" in diff: 
                        update_tree = diff.added.gestures.copy() \
                            if "updated" in diff else diff.added.gestures
                    if "updated" in diff:
                        if update_tree is None:
                            update_tree = diff.updated.gestures
                        else:
                            update_tree.update(diff.updated.gestures, reuse=True)
                    if update_tree is not None:
                        for gid, gdiff in update_tree.items():
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
                                    prev.s = gid
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
                    if ("removed", "gestures") in diff:
                        for gid in diff.removed.gestures.keys():
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
                                                self.__class__.__name__)
                        alive = list(profilestate[1].keys())
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
                        forward = ExtensibleTree()
                        forward.osc = osc.Bundle(product.get("timetag"), msgs)
                        forward.data = forward.osc.encode()
                        self._postProduct(forward)

# ---------------------------------------------------------------------

def TuioOutput(url):
    """
    Return a StateToTuio from an URL with scheme="tuio*".
     examples:
      test.osc.bz2
      /home/boing/gestures/test.osc.bz2
      tuio:///home/boing/gestures/test.osc.bz2
      tuio://localhost:3333
      tuio.udp://127.0.0.1:3333 
      tuio.tcp://127.0.0.1:3333 
    """
    kwargs = {}
    req = url.query.data.get('req')
    if req is not None: kwargs["requests"] = parseRequests(req)
    output = StateToTuio(**kwargs)
    if not isinstance(url, URL): url = URL(str(url))
    if url.kind in (URL.ABSPATH, URL.RELPATH) \
            or url.scheme=="tuio.file" \
            or (url.scheme=="tuio" and not str(url.site)):
        consumer = LogFile(File(url, File.WriteOnly), parent=output)
        consumer.subscribeTo(output)
    elif url.scheme in ("tuio", "tuio.udp"):
        consumer = DataWriter(UdpSender(url), parent=output)
        consumer.subscribeTo(output)
    elif url.scheme.endswith("tuio.tcp"):
        consumer = SlipDataWriter(TcpConnection(url), parent=output)
        consumer.outputDevice().setOption("nodelay")
        consumer.subscribeTo(output)
    else:
        output = None
        print("Unrecognized TUIO output: %s"%str(url))
    return output
