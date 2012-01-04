# -*- coding: utf-8 -*-
#
# boing/utils/Output.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import os
import sys

from boing.eventloop.OnDemandProduction import DumpConsumer
#from boing.multitouch.GestureBuffer import GestureBuffer
from boing.multitouch.GestureViz import GestureViz
from boing.eventloop.MappingEconomy import parseRequests
from boing.json.JSONTunnel import JSONWriter
from boing.tuio.StateToTuio import TuioOutput
from boing.utils.IODevice import IODevice
from boing.utils.StatProducer import StatProducer
from boing.utils.TextIO import TextWriter
from boing.url import URL
        
def Output(url):
    if not isinstance(url, URL): url = URL(str(url))
    output = None
    kwargs = {}
    if url.kind in (URL.ABSPATH, URL.RELPATH) \
            or url.scheme.startswith("tuio"):        
        output = TuioOutput(url)
    if url.scheme.startswith("json"):
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
        output = GestureViz(**kwargs)
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
    else:
        print("Unrecognized output URL:", str(url))
    return output

# -------------------------------------------------------------------

class _TerminalWriter(TextWriter):

    def __init__(self, clear=False, parent=None):
        TextWriter.__init__(self, IODevice(sys.stdout), parent=parent)
        self.clear = clear
            
    def _consume(self, products, producer):
        if self.clear:
            if sys.platform=="linux2": os.system("clear")
            elif sys.platform=="win32": os.system("CLS")
        TextWriter._consume(self, products, producer)
