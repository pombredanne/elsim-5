# This file is part of Elsim
#
# Copyright (C) 2012, Anthony Desnos <desnos at t0t0.fr>
# All rights reserved.
#
# Elsim is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Elsim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Elsim.  If not, see <http://www.gnu.org/licenses/>.

import re
from operator import itemgetter
import mmh3

from elsim import debug, get_debug
import elsim
from elsim.similarity import Compress
from elsim.filters import FilterEmpty, filter_sort_meth_basic


class CheckSumText:
    def __init__(self, s1, sim):
        """
        :param Text s1: the element
        :param elsim.similarity.Similarity sim: the similarity module
        """
        self.s1 = s1
        self.sim = sim
        self.buff = s1.string
        self.entropy = 0.0
        self.signature = None

    def get_signature(self):
        if self.signature == None:
            raise ValueError("no signature set!")
        self.signature_entropy = self.sim.entropy(self.signature)

        return self.signature

    def get_signature_entropy(self):
        if self.signature == None:
            raise ValueError("no signature set!")
        self.signature_entropy = self.sim.entropy(self.signature)

        return self.signature_entropy

    def get_entropy(self):
        return self.entropy

    def get_buff(self):
        return self.buff


class Text:
    """
    Basic Wrapper for text

    trailing and leading whitespaces are removed from the text.
    """
    def __init__(self, element, sim):
        self.string = element.strip(b' ')
        self.sim = sim

        # Lazy load them later, if necessary
        self.__hash = None
        self.__checksum = None

    def __str__(self):
        return repr(self.string)

    @property
    def checksum(self):
        if not self.__checksum:
            self.__checksum = CheckSumText(self, self.sim)
        return self.__checksum

    @property
    def hash(self):
        if not self.__hash:
            self.__hash = mmh3.hash128(self.checksum.get_buff())
        return self.__hash

    def __repr__(self):
        return str(self)


FILTERS_TEXT = {
    elsim.FILTER_ELEMENT_METH: lambda element, iterable, sim: Text(element, sim),
    elsim.FILTER_SIM_METH: lambda sim, element1, element2: sim.ncd(element1.checksum.get_buff(), element2.checksum.get_buff()),
    elsim.FILTER_SORT_METH: filter_sort_meth_basic,
    elsim.FILTER_SKIPPED_METH: FilterEmpty,
}


class ProxyText:
    """
    ProxyText can be used as a proxy for Elsim which handles
    Text by splitting it at any sentence into words.
    The sentences are then the iterable and are getting compared.

    In order to compare a text, bytes must be supplied.
    So either encode the text yourself, or use the encoding parameter
    to let the Proxy encode the text.
    """
    def __init__(self, buff, encoding=None):
        """
        :param buff: the bytes of the text, or str if encoding is given
        :param str encoding: name of the encoding to encode str to bytes
        """
        if isinstance(buff, bytes):
            self.buff = buff
        elif encoding is not None:
            self.buff = buff.encode(encoding)
        else:
            raise ValueError("You must specify an encoding or encode the string to bytes yourself!")

    def __iter__(self):
        # split elements at the following characters: [;,-.?:!]
        # newlines are treated like whitespaces
        # TODO: actually there are probably better methods of detecting sentences...
        # TODO: what about other characters which we might want to replace to whitespace like tabs?
        yield from re.split(br'; |, |-|\.|\?|:|!', self.buff.replace(b"\n", b" "))

