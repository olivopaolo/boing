# -*- coding: utf-8 -*-
#
# boing/net/osc.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

# Based on
#  "The Open Sound Control 1.0 Specification"
#     http://opensoundcontrol.org/spec-1_0
#  "Features and Future of Open Sound Control version 1.1 for NIME"


"""The module :mod:`boing.net.osc` provides methods and classes for
handling OSC formatted messages.

Usage example::

   >>> import sys
   >>> import boing.net.osc as osc
   >>> source = osc.Message("/tuio/2Dcur", "ss", "source", "test")
   >>> alive = osc.Message("/tuio/2Dcur", "ss", "alive", "1")
   >>> bundle = osc.Bundle(None,
                           (source, alive,
                            osc.Message("/tuio/2Dcur", "si", "fseq", 1)))
   >>> data = bundle.encode()
   >>> print(data)
   b'#bundle\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00 /tuio/2Dcur\x00,ss\x00source\x00\x00test\x00\x00\x00\x00\x00\x00\x00\x1c/tuio/2Dcur\x00,ss\x00alive\x00\x00\x001\x00\x00\x00\x00\x00\x00\x1c/tuio/2Dcur\x00,si\x00fseq\x00\x00\x00\x00\x00\x00\x00\x01'
   >>> packet = osc.decode(data)
   >>> print(packet)
   <Bundle instance at 0x1b756d0 [@None, 3 element(s)]>
   >>> packet.debug(sys.stdout)
   Bundle IMMEDIATELY
    | /tuio/2Dcur ss 'source' 'test'
    | /tuio/2Dcur ss 'alive' '1'
    | /tuio/2Dcur si 'fseq' 1

"""

import abc
import io
import datetime
import struct
import traceback

from boing.net import ntp
from boing.utils import assertIsInstance

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

class Packet(metaclass=abc.ABCMeta):

    def __init__(self):
        """Abstact base container of OSC data."""
        pass

    @abc.abstractmethod
    def encode(self):
        """Return the encoded representation of this packet."""
        raise NotImplementedError()

    @abc.abstractmethod
    def debug(self, out, indent=""):
        """Write to *out* a string representation of the OSC
        packet. The argument *indent* can be used to format the
        output."""
        raise NotImplementedError()
# -----------------------------------------------------------------

class EncodedPacket(Packet):

    def __init__(self, data):
        """Container for the encoded OSC packet *data*."""
        self.data = data
        self.source = None

    def encode(self):
        return self.data

    def decode(self):
        """Return the decoded representation of this packet, that is an
        instance of the class :class:`Bundle` or :class:`Message`."""
        return decode(self.data)

    def debug(self, out, indent=""):
        print(indent+self.__class__.__name__, len(self.data), "bytes", file=out)

# -----------------------------------------------------------------

class Message(Packet):

    def __init__(self, address, typetags="", *arguments):
        """:class:`Packet` object representing an OSC Message. The
        argument *address* must be a string begginning with the
        character ``/`` (forward slash). The argument *typetags* must
        be a string composed by sequence of characters corresponding
        exactly to the sequence of OSC arguments in the given
        message. *arguments* is the list of object contained in the
        OSC Message.

        """
        self.address = assertIsInstance(address, str)
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

    def debug(self, out, indent=""):
        print(indent+self.address, self.typetags, end=' ', file=out)
        for argument in self.arguments:
            print(repr(argument), end=' ', file=out)
        print(file=out)

# -----------------------------------------------------------------

class Bundle(Packet):

    def __init__(self, timetag, elements):
        """:class:`Packet` object representing an OSC Bundle. The
        argument *timetag* must be a :class:`datetime.datetime`
        instance or ``None``, while *elements* should be the list of
        :class:`Packet` objects contained in the bundle.

        """
        self.timetag = assertIsInstance(timetag, None, datetime.datetime)
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

    def debug(self, out, indent=""):
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
    """Return the :class:`Packet` object decoded from the bytestring
    *data*. The argument *source* can be specified to set the packet
    source."""
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
    """This method modifies the OSC bundles's timetag so that the
    first of the stream has timetag as startTime and the distance
    between bundles is dependant from speedFactor. When recursive is
    True also the internal bundles are affected."""
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

from boing.net import Encoder as _AbstractEncoder
from boing.net import Decoder as _AbstractDecoder

class Encoder(_AbstractEncoder):
    """The Encoder is able to encode OSC packet objects into byte strings.

    """
    def encode(self, obj):
        """Return the bytestring obtained from serializing the OSC
        packet *obj*."""
        return obj.encode()

    def reset(self):
        """NOP method."""
        pass

class Decoder(_AbstractDecoder):
    """The Decoder is able to convert valid byte string objects into
    OSC Packet objects.

    """
    def decode(self, obj):
        """Return the list of OSC packets decoded from the bytestring
        *obj*."""
        return decode(obj),

    def reset(self):
        """NOP method."""
        pass
