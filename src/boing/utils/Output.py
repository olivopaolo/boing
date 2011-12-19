# -*- coding: utf-8 -*-
#
# boing/utils/Output.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from boing.eventloop.OnDemandProduction import DumpConsumer
#from boing.multitouch.GestureBuffer import GestureBuffer
from boing.multitouch.GestureViz import GestureViz
from boing.eventloop.MappingEconomy import parseRequests
from boing.tuio.StateToTuio import TuioOutput
from boing.url import URL

def Output(url):
    if not isinstance(url, URL): url = URL(str(url))
    output = None
    args = {}
    if url.kind in (URL.ABSPATH, URL.RELPATH) \
            or url.scheme.startswith("tuio"):        
        output = TuioOutput(url)
    elif url.scheme=="dump":
        req = url.query.data.get('req')
        if req is not None: args["requests"] = parseRequests(req)
        src = url.query.data.get('src')
        if src is not None: args["dumpsrc"] = src.lower()!="false"
        dest = url.query.data.get('dest')
        if dest is not None: args["dumpdest"] = dest.lower()!="false"
        count = url.query.data.get('count')
        if count is not None: args["count"] = count.lower()!="false"
        hz = url.query.data.get('hz')
        if hz is not None:
            try: args["hz"] = float(hz)
            except ValueError: 
                print("ValueError: hz must be numeric, not %s"%
                      hz.__class__.__name__)
        output = DumpConsumer(**args)
    elif url.scheme=="viz":
        req = url.query.data.get('req')
        if req is not None: args["requests"] = parseRequests(req)
        if 'hz' in url.query.data:
            hz = url.query.data['hz']
            if hz.lower()=="none": args["fps"] = None
            else:
                try: args["fps"] = float(hz)
                except ValueError: 
                    print("ValueError: hz must be numeric, not %s"%
                          hz.__class__.__name__)
        if "antialiasing" in url.query.data:
            args["antialiasing"] = url.query.data["antialiasing"].lower()!="false"
        output = GestureViz(**args)
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
        '''elif url.scheme=="buffer":
        req = url.query.data.get('req')
        if req is not None: args["requests"] = parseRequests(req)
        if 'hz' in url.query.data:
            hz = url.query.data['hz']
            if hz.lower()=="none": args["hz"] = None
            else:
                try: args["hz"] = float(hz)
                except ValueError: 
                    print("ValueError: hz must be numeric, not %s"%
                          hz.__class__.__name__)
        output = GestureBuffer(**args)'''
    else:
        print("Unrecognized output URL:", str(url))
    return output

