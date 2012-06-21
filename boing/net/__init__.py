# -*- coding: utf-8 -*-
#
# boing/net/__init__.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

"""The *boing.net* module provides classes and methods to ease the
usage of sockets and different networking encoding like json, osc,
slip, etc.

"""

import abc
import itertools

from boing.utils import assertIsInstance

class Encoder(metaclass=abc.ABCMeta):
    """The Encoder class is the abstract base class for implementing
    the encoders of all the different encodings.

    """
    @abc.abstractmethod
    def encode(self, obj):
        """Return the result obtained from encoding *obj*."""
        raise NotImplementedError()

    @abc.abstractmethod
    def reset(self):
        """Reset the encoder."""
        raise NotImplementedError()

class Decoder(metaclass=abc.ABCMeta):
    """The Decoder class is the abstract base class for implementing
    the decoders of all the different encodings.

    The Decoder class implements the composite pattern. Many decoders
    can be put in sequence into a single composed decoder using the
    sum operator.

    """
    @abc.abstractmethod
    def decode(self, obj):
        """Return the list of objects obtained from decoding *obj*."""
        raise NotImplementedError()

    @abc.abstractmethod
    def reset(self):
        """Reset the decoder."""
        raise NotImplementedError()

    def __add__(self, other):
        assertIsInstance(other, Decoder, None)
        return self if other is None else _CompositeDecoder(self, other)

    def __radd__(self, other):
        return self if other is None else NotImplemented

class _CompositeDecoder(Decoder):
    """The _CompositeDecoder implements the Composite design
    pattern. It owns a sequence of child decoders; to decode an object
    it applies in sequence the child decoders.
    """
    def __init__(self, *decoders):
        super().__init__()
        self._sequence = list()
        for decoder in decoders:
            assertIsInstance(decoder, Decoder)
            if isinstance(decoder, _CompositeDecoder):
                self._sequence.extend(decoder.sequence())
            else:
                self._sequence.append(decoder)

    def sequence(self):
        """Return the sequence of child decoders."""
        return self._sequence

    def decode(self, obj):
        """Return the list of objects obtained from decoding *obj*."""
        return self._recursiveDecode(obj, 0)

    def reset(self):
        """Reset the decoder."""
        for decoder in self._sequence:
            decoder.reset()

    def _recursiveDecode(self, obj, index):
        """Invoke the current decoder and iterate recursively."""
        if index==len(self._sequence): rvalue = obj,
        else:
            l = lambda decoded: self._recursiveDecode(decoded, index+1)
            rvalue = tuple(
                itertools.chain(*map(l, self._sequence[index].decode(obj))))
        return rvalue



