# -*- coding: utf-8 -*-
#
# boing/net/bytes.py
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

"""The bytes module implements the adapter design pattern by providing
the standard string encoding functionalities as Encoder and Decoder
objects.

"""

def encode(string, encoding="utf-8", errors="strict"):
    """Return an encoded version of *string* as a bytes
    object. Default encoding is 'utf-8'. *errors* may be given to set
    a different error handling scheme. The default for errors is
    'strict', meaning that encoding errors raise a UnicodeError. Other
    possible values are 'ignore', 'replace', 'xmlcharrefreplace',
    'backslashreplace'."""
    return string.encode(encoding, errors)

def decode(data, encoding="utf-8", errors="strict"):
    """Return a string decoded from the given bytes. Default
    *encoding* is 'utf-8'. *errors* may be given to set a different
    error handling scheme. The default for errors is 'strict', meaning
    that encoding errors raise a UnicodeError. Other possible values
    are 'ignore', 'replace' and any other name registered via
    codecs.register_error()."""
    return data.decode(encoding, errors)

# -------------------------------------------------------------------

from boing.net import Encoder as _AbstractEncoder
from boing.net import Decoder as _AbstractDecoder

class Encoder(_AbstractEncoder):
    """The Encoder is able to produce encoded version of string
    objects as byte objects.

    """
    def __init__(self, encoding="utf-8", errors="strict"):
        super().__init__()
        self.encoding = encoding
        self.errors = errors

    def encode(self, string):
        """Return an encoded version of *string* as a bytes
        object."""
        return encode(string, self.encoding, self.errors)

    def reset(self):
        """NOP method."""
        pass


class Decoder(_AbstractDecoder):
    """The Decoder is able to convert byte objects into strings.

    """
    def __init__(self, encoding="utf-8", errors="strict"):
        super().__init__()
        self.encoding = encoding
        self.errors = errors

    def decode(self, data):
        """Return the list of strings decoded from the given bytes."""
        return decode(data, self.encoding, self.errors),

    def reset(self):
        """NOP method."""
        pass
