# -*- coding: utf-8 -*-
#
# boing/slip/__init__.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

# Based on
#     Nonstandard for transmission of IP datagrams over serial lines: SLIP
#     http://tools.ietf.org/html/rfc1055

END     = 0o300 # indicates end of packet
ESC     = 0o333 # indicates byte stuffing
ESC_END = 0o334 # ESC ESC_END means END data byte
ESC_ESC = 0o335 # ESC ESC_ESC means ESC data byte

def encode(data):
    encoded = bytearray()
    encoded.append(END)
    for c in data:
        if c==END:
            encoded.append(ESC)
            encoded.append(ESC_END)
        elif c==ESC:
            encoded.append(ESC)
            encoded.append(ESC_ESC)
        else:            
            encoded.append(c)
    encoded.append(END)
    return bytes(encoded)

def decode(data, previous=None):
    decoded = previous if previous else bytearray()    
    result, prev = [], None
    for c in data:
        if prev==ESC:
            if c==ESC_END:
                decoded.append(END)
            elif c==ESC_ESC:
                decoded.append(ESC)
            else:
                decoded.append(bytes((c,))) # protocol violation...
        else:
            if c==END:
                if decoded: result.append(bytes(decoded))
                decoded = bytearray()
            elif c==ESC:
                pass
            else:
                decoded.append(c)
        prev = c
    return result, decoded

# -----------------------------------------------------------------

if __name__=="__main__":
    import sys
    encoded = ""
    line = b"boing-test"
    encoded = encode(line)
    print(len(encoded), repr(encoded))
    print(decode(encoded))
