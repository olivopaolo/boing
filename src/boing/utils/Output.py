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
        hz = url.query.data.get('hz')
        if hz is not None:
            if hz.lower()=="none": args["fps"] = None
            else:
                try: args["fps"] = float(hz)
                except ValueError: 
                    print("ValueError: hz must be numeric, not %s"%
                          hz.__class__.__name__)
        width = url.query.data.get('w')
        if width is not None:
            try: args["width"] = int(width)
            except ValueError: 
                print("ValueError: width must be integer, not %s"%
                      width.__class__.__name__)
        height = url.query.data.get('h')
        if height is not None:
            try: args["height"] = int(height)
            except ValueError: 
                print("ValueError: height must be integer, not %s"%
                      height.__class__.__name__)
        output = EventViz(**args)
        output.show()
        output.raise_()
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

