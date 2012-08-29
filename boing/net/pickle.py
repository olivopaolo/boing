# -*- coding: utf-8 -*-
#
# boing/net/pickle.py
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

"""The pickle module provides methods and classes for supporting Python
object serialization. It uses the python pickle standard module.

Encoder and Decoder classes provide a standard interface for the pickle
encoding.

"""

import pickle as _pickle

def encode(obj, protocol=None):
    """Return the pickled representation of *obj* as a bytes object.

    The optional protocol argument tells the pickler to use the given
    protocol; supported protocols are 0, 1, 2, 3. The default protocol
    is 3; a backward-incompatible protocol designed for Python 3.0.

    Specifying a negative protocol version selects the highest
    protocol version supported. The higher the protocol used, the more
    recent the version of Python needed to read the pickle produced."""
    return _pickle.dumps(obj, protocol)

def decode(data):
    """Read a pickled object hierarchy from the bytes object *data*
    and return the reconstituted object hierarchy specified therein.

    The protocol version of the pickle is detected automatically, so
    no protocol argument is needed. Bytes past the pickled object’s
    representation are ignored."""
    return _pickle.loads(data)

# -------------------------------------------------------------------

from boing.net import Encoder as _AbstractEncoder
from boing.net import Decoder as _AbstractDecoder

class Encoder(_AbstractEncoder):
    """The Encoder is able to serialize Python objects into pickle
    bytestrings.

    """
    def encode(self, obj, protocol=None):
        """Return the pickled representation of *obj* as a bytes object.

        The optional protocol argument tells the pickler to use the given
        protocol; supported protocols are 0, 1, 2, 3. The default protocol
        is 3; a backward-incompatible protocol designed for Python 3.0.

        Specifying a negative protocol version selects the highest
        protocol version supported. The higher the protocol used, the more
        recent the version of Python needed to read the pickle produced."""
        return encode(obj, protocol)

    def reset(self):
        """NOP method."""
        pass

class Decoder(_AbstractDecoder):
    """The Decoder object is able to decode pickle bytestrings into
    the corrispetive objects hierarchy.

    """
    def decode(self, data):
        """Read a pickled object hierarchy from the bytes object *data*
        and return the reconstituted object hierarchy specified therein.

        The protocol version of the pickle is detected automatically, so
        no protocol argument is needed. Bytes past the pickled object’s
        representation are ignored."""
        return decode(data),

    def reset(self):
        """NOP method."""
        pass
