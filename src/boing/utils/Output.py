# -*- coding: utf-8 -*-
#
# boing/utils/Output.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from boing.eventloop.OnDemandProduction import DumpConsumer
from boing.multitouch.EventViz import EventViz
from boing.url import URL

def Output(url):
    if not isinstance(url, URL): url = URL(str(url))
    output = None
    args = {}
    rest = url.query.data.get('rest')
    if rest is not None: args["restrictions"] = parseRestrictions(rest)
    if url.scheme=="dump":
        src = url.query.data.get('src')
        if src is not None: args["dumpsrc"] = src.lower()!="false"
        dest = url.query.data.get('dest')
        if dest is not None: args["dumpdest"] = dest.lower()!="false"
        hz = url.query.data.get('hz')
        if hz is not None:
            try: args["hz"] = float(hz)
            except ValueError: 
                print("ValueError: hz must be numeric, not %s"%
                      hz.__class__.__name__)
        output = DumpConsumer(**args)
    elif url.scheme=="viz":
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
        output = EventViz(**args)
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
        """elif url.scheme.startswith("tuio"):        
        output = TuioOutput(url)"""
    else:
        print("Unrecognized output URL:", str(url))
    return output

'''
def UrlToOutputClass(url):
    outputclass = None
    if not isinstance(url, URL): url = URL(str(url))
    if url.scheme=="dump": outputclass = DumpConsumer
    elif url.scheme=="viz": outputclass = EventViz
    elif url.scheme.startswith("tuio"): outputclass = TuioOutputClass(url)
    return outputclass'''

def parseRestrictions(restrictions):
    try:
        rest = []
        path = []
        string = restrictions
        while string:
            part, comma, string = string.partition(",")
            index = part.find("(")
            if index==-1:
                index = part.find(")")
                if index==-1:
                    if path: path.append(part.strip())
                    else: rest.append(part.strip())
                elif index==len(part)-1:
                    if path: 
                        path.append(part[:-1].strip())
                        rest.append(tuple(path))
                        path = []
                    else: raise Exception()
                else: raise Exception()
            elif index==0: 
                index = part.find(")")
                if index==-1:
                    if path: raise Exception()
                    else: path.append(part[1:].strip())
                elif index==len(part)-1:
                    if path: raise Exception()
                    else: rest.append(part[1:-1].strip())
                else: raise Exception()            
            else: raise Exception()
        if path: raise Exception()
    except Exception: 
        print("Wrong format: %s"%restrictions)
    else: 
        return tuple(rest)

