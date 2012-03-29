# -*- coding: utf-8 -*-
#
# boing/net/osc.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

# Based on
#  "The Open Sound Control 1.0 Specification"
#     http://opensoundcontrol.org/spec-1_0
#  "Features and Future of Open Sound Control version 1.1 for NIME"

import io
import datetime
import struct
import traceback

import boing.utils.ntp as ntp

# -----------------------------------------------------------------

# Constants
#   T - True
#   F - False
#   N - Null (aka nil, None, etc)
#   I - Impulse (aka “bang” or “Infinitum”), used for event triggers
#
# Variables
#   i - Integer: two’s complement int32
#   f - Float: IEEE float32
#   s - NULL-terminated ASCII string
#   b - Blob, (aka byte array) with size
#   t - Timetag: an OSC timetag in NTP format

class IMPULSE(object): pass

IMPULSE     = IMPULSE()
IMMEDIATELY = 0x0000000000000001 # FIXME

SUPPORTED_TYPES = "TFNIifsbt"

def _pad(size, n=4):
    mod = size%n
    if mod==0: return size
    return size + n-mod
   
def _arg_type(arg):
    if arg is True: return 'T'
    elif arg is False: return 'F'
    elif arg is None: return 'N'
    elif arg is IMPULSE: return 'I'
    elif isinstance(arg, int): return 'i'
    elif isinstance(arg, float): return 'f'
    elif isinstance(arg, str): return 's'
    elif isinstance(arg, bytes): return 'b'
    elif isinstance(arg, datetime.datetime): return 't'
    else: raise TypeError("No matching OSC type")

def _arg_encode(arg, typetag):
    if typetag=='i':
        return struct.pack("!i", int(arg))
    elif typetag=='f':
        return struct.pack("!f", float(arg))
    elif typetag=='s':
        if not isinstance(arg, bytes): arg = str(arg).encode()
        size = _pad(len(arg)+1)
        return struct.pack("!%ds"%size, arg)
    elif typetag=='b':
        if not isinstance(arg, bytes): arg = str(arg).encode()
        realsize = len(arg)
        size = _pad(realsize)
        return struct.pack("!i%ds"%size, realsize, arg)
    elif typetag=='t':
        if arg is None:
            return struct.pack("!q", IMMEDIATELY)
        if type(arg) is datetime.datetime:
            return ntp.ntpEncode(ntp.datetime2ntp(arg))
        raise ValueError("Time tag should be a datetime.datetime object or None for IMMEDIATELY")
    else:
        raise TypeError("Unsupported type tag (%s)"%typetag)

def _arg_decode(data, typetag):
    if typetag=='T': arg = None
    elif typetag=='F': arg = None
    elif typetag=='N': arg = None
    elif typetag=='I': arg = None
    elif typetag=='i':
        if len(data)<4: raise ValueError("Wrong data size for an int")
        arg, data = struct.unpack("!i", data[:4])[0], data[4:]
    elif typetag=='f':
        if len(data)<4: raise ValueError("Wrong data size for a float")
        arg, data = struct.unpack("!f", data[:4])[0], data[4:]
    elif typetag=='s':
        eos = data.find(b'\0')
        if eos==-1: raise ValueError("Not a string")
        size = _pad(eos+1)
        arg, data = data[:eos].decode(), data[size:]
    elif typetag=='b':
        realsize = struct.unpack("!i", data[0:4])[0]
        size = _pad(realsize)
        if len(data)<size: 
            raise ValueError("Wrong data size for a %d bytes blob"%realsize)
        arg, data = data[4:4+realsize], data[size:]
    elif typetag=='t':
        if len(data)<8: raise ValueError("Wrong data size for a time tag")
        argdata, data = data[:8], data[8:]
        if struct.unpack("!q", argdata)[0]==IMMEDIATELY: arg = None
        else: arg = ntp.ntp2datetime(ntp.ntpDecode(argdata))
    else: raise TypeError("Unsupported type tag (%s)"%typetag)
    return (arg, data)

# -----------------------------------------------------------------

class Packet(object):
    pass

# -----------------------------------------------------------------

class EncodedPacket(Packet):
    
    def __init__(self, data):
        self.data = data
        self.source = None
        
    def encode(self):
        return self.data

    def decode(self):
        return decode(self.data)

    def debug(self, out, indent=''):
        print(indent+self.__class__.__name__, len(self.data), "bytes", file=out)
    
# -----------------------------------------------------------------

class Message(Packet):

    def __init__(self, address, typetags="", *arguments):
        if not isinstance(address, str):
            raise TypeError("Expected string value:", address)
        self.address = address
        self.typetags = typetags
        self.arguments = arguments
        self.source = None # source is not encoded
        
    def __str__(self):
        return """<%s instance at 0x%x [%s, %s, %d argument(s)]>"""%(
            self.__class__.__name__, id(self), 
            repr(self.address), repr(self.typetags), len(self.arguments))
    
    def encode(self):
        data = io.BytesIO()
        data.write(_arg_encode(self.address, 's'))
        typetags = self.typetags
        if typetags is None: typetags = "".join(map(_arg_type, self.arguments))
        elif len(self.typetags.strip('TFNI'))!=len(self.arguments): 
            raise TypeError("Typetag error")
        data.write(_arg_encode(','+typetags, 's'))
        ia = 0
        for it in range(len(typetags)):
            typetag = typetags[it]
            if typetag not in ('T', 'F', 'N', 'I'):
                data.write(_arg_encode(self.arguments[ia], typetag))
                ia = ia + 1
        return data.getvalue()

    def debug(self, out, indent=''):
        print(indent+self.address, self.typetags, end=' ', file=out)
        for argument in self.arguments:
            print(repr(argument), end=' ', file=out)
        print(file=out)

# -----------------------------------------------------------------

class Bundle(Packet):

    def __init__(self, timetag, elements):
        self.timetag = timetag
        self.elements = elements
        self.source = None # source is not encoded
        
    def __str__(self):
        return """<%s instance at 0x%x [@%s, %d element(s)]>"""%(
            self.__class__.__name__, id(self),
            repr(self.timetag), len(self.elements))

    def encode(self):
        data = io.BytesIO()
        data.write(_arg_encode("#bundle",'s'))
        data.write(_arg_encode(self.timetag,'t'))
        for element in self.elements:
            try:
                edata = element.encode()
                data.write(_arg_encode(len(edata),'i'))
                data.write(edata)
            except:
                print("Warning: ignoring OSC Message while encoding Bundle")
                traceback.print_exc()
        return data.getvalue()

    def debug(self, out, indent=''):
        if self.timetag is None:
            when = "IMMEDIATELY"
        else:
            when = '@%s'%self.timetag.isoformat()
        print(indent+self.__class__.__name__, when, file=out)
        indent = indent+' | '
        for element in self.elements:
            element.debug(out, indent)

# -----------------------------------------------------------------

def decode(data, source=None):
    s, part = _arg_decode(data, 's')
    if s=="#bundle":
        timetag, part = _arg_decode(part, 't')
        elements = []
        while len(part)>0:
            size, part = _arg_decode(part, 'i')
            elements.append(decode(part[:size], source))
            part = part[size:]
        packet = Bundle(timetag, elements)
    else:
        if s[0]!='/': 
            print(s)
            raise ValueError("Address pattern should start with '/'")
        typetags, part = _arg_decode(part,'s')
        if typetags[0]!=',': 
            raise ValueError("Type tag string should start with ','")
        arguments = []
        for tag in typetags[1:]:
            arg, part = _arg_decode(part, tag)
            if arg is not None: arguments.append(arg)
        packet = Message(s, typetags[1:], *arguments)
    packet.source = source
    return packet

# -----------------------------------------------------------------

def dict2bundle(d, address):
    msgs = []
    for k, (f,v) in d.items():
        fmt, args = "s"+f, [k]
        if isinstance(v, list) or isinstance(v, tuple): args.extend(v)
        else: args.append(v)
        msg = Message(address, fmt, *args)
        msgs.append(msg)
    return Bundle(None, msgs)
                    
def bundle2dict(b, address):
    d = {}
    for msg in b.elements:
        if msg.address==address:
            key, value = msg.arguments[0], msg.arguments[1:]
            if len(value)==1: value = value[0]
            d[key] = value
    return d

# -----------------------------------------------------------------

def streamTimeWarp(osc_stream, startTime=None, speedFactor=1, recursive=False):
    """ This method modifies the OSC bundles's timetag so that the
    first of the stream has timetag as startTime and the distance
    between bundles is dependant from speedFactor. When recursive is
    True also the internal bundles are affected.
    """
    def __bundleTimeWarp(osc_bundle) :
        """ Recoursive method for exploring bundles inside bundles. """
        timedelta = osc_bundle.timetag - t0
        microseconds = timedelta.days * 24 *60 * 60 * 1000000 + timedelta.seconds * 1000000 + timedelta.microseconds
        microseconds = microseconds / speedFactor        
        osc_bundle.timetag = startTime + datetime.timedelta(microseconds=microseconds)
        if recursive :
            # recursive exploration
            for elem in osc_bundle.elements :
                if isinstance(elem, Bundle) :
                    bundleTimeWarp(elem, t0, startTime, speedFactor)
    
    t0 = None
    for packet in osc_stream :
        if isinstance(packet, Bundle):
            if t0 is None :
                t0 = packet.timetag
                if startTime is None :
                    startTime = t0
            __bundleTimeWarp(packet)

# -----------------------------------------------------------------

if __name__=="__main__":
    import math
    import sys
    import traceback
    for msg1 in (
        Message("/msg","iii",23,10,2009),
        Message("/msg","","this should fail", "bad typetag"),
        Message("/msg","TFNIi",23),
        Message("/msg",None,23),
        Message("/msg",None,math.pi),
        Message("/msg",None,"this is a string"),
        Message("/msg",None,"this one\0should be passed as a buffer"),
        Message("/msg","b","this is a string\0 passed as a buffer"),
        Bundle(datetime.datetime.now(), 
               (Message("/bndl",None,1), Message("/bndl",None,2.0))),
        Bundle(None, 
               (Bundle(None,(Message("/bndl",None,1),Message("/bndl",None,2))), 
                Message("/bndl",None,2.0)))
        ):
        print("TST", msg1)
        try:
            data = msg1.encode()
            print("OSC",repr(data))
            msg2 = decode(data)
            msg2.debug(sys.stdout)
        except:
            print("Test failed:", sys.exc_info()[1])
            traceback.print_exc()
        print()
