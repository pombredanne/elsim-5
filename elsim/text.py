#!/usr/bin/env python

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

import hashlib
import re
from operator import itemgetter

from elsim import debug, get_debug
import elsim
from elsim.similarity import Compress
from elsim.filters import filter_sim_value_meth


class CheckSumText:
    def __init__(self, s1, sim):
        """
        :param bytes s1: the element
        :param elsim.similarity.SIMILARITY sim: the similarity module
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


def filter_sim_meth_basic(sim, m1, m2):
    # sim.set_compress_type(Compress.XZ)
    ncd1 = sim.ncd(m1.checksum.get_buff(), m2.checksum.get_buff())
    return ncd1


def filter_sort_meth_basic(j, x, value):
    z = sorted(x.items(), key=itemgetter(1))

    if get_debug():
        for i in z:
            debug("\t %s %f" % (i[0].get_info(), i[1]))

    if z[:1][0][1] > value:
        return []

    return z[:1]


class Text:
    def __init__(self, e, el):
        self.string = el

        nb = 0
        for i in range(0, len(self.string)):
            if self.string[i] == " ":
                nb += 1
            else:
                break

        self.string = self.string[nb:]
        self.sha256 = None

    def get_info(self):
        return "%d '%s'" % (len(self.string), repr(self.string))

    def set_checksum(self, fm):
        self.sha256 = hashlib.sha256(fm.get_buff()).hexdigest()
        self.checksum = fm

    def getsha256(self):
        return self.sha256

    def __repr__(self):
        return self.get_info()


class FilterNone:
    """
    This filter removes all empty or only whitespace elements
    """
    @staticmethod
    def skip(element):
        if element in (b'', b' '):
            return True

        return False


FILTERS_TEXT = {
    elsim.FILTER_ELEMENT_METH: lambda element, iterable: Text(iterable, element),
    elsim.FILTER_CHECKSUM_METH: lambda m1, sim: CheckSumText(m1, sim),
    elsim.FILTER_SIM_METH: filter_sim_meth_basic,
    elsim.FILTER_SORT_METH: filter_sort_meth_basic,
    elsim.FILTER_SORT_VALUE: 0.6,
    elsim.FILTER_SKIPPED_METH: FilterNone(),
    elsim.FILTER_SIM_VALUE_METH: filter_sim_value_meth,
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

