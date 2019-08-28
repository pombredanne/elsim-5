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

import mmh3
from operator import itemgetter

from elsim import error, warning, debug, set_debug, get_debug
import elsim
from elsim.filters import FilterNone, filter_sort_meth_basic


class CheckSumFunc(object):
    def __init__(self, f, sim):
        self.f = f
        self.sim = sim
        self.buff = ""
        self.entropy = 0.0
        self.signature = None

        for i in self.f.get_instructions():
            self.buff += i.get_mnemonic()

        self.entropy = sim.entropy(self.buff)

    def get_signature(self):
        if self.signature == None:
            self.signature = self.buff
            self.signature_entropy = self.sim.entropy(self.signature)

        return self.signature

    def get_signature_entropy(self):
        if self.signature == None:
            self.signature = self.buff
            self.signature_entropy = self.sim.entropy(self.signature)

        return self.signature_entropy

    def get_entropy(self):
        return self.entropy

    def get_buff(self):
        return self.buff


def filter_checksum_meth_basic(f, sim):
    return CheckSumFunc(f, sim)


def filter_sim_meth_basic(sim, m1, m2):
    ncd2 = sim.ncd(m1.checksum.get_buff(), m2.checksum.get_buff())
    return ncd2


class Instruction(object):
    def __init__(self, i):
        self.mnemonic = i[1]

    def get_mnemonic(self):
        return self.mnemonic


class Function(object):
    def __init__(self, e, el):
        self.function = el
        self.__hash = None

    def get_instructions(self):
        for i in self.function.get_instructions():
            yield Instruction(i)

    def get_nb_instructions(self):
        return len(self.function.get_instructions())

    def __str__(self):
        return self.function.name

    def set_checksum(self, fm):
        self.__hash = mmh3.hash128(fm.get_buff())
        self.checksum = fm

    @property
    def hash(self):
        return self.__hash


def filter_element_meth_basic(el, e):
    return Function(e, el)


FILTERS_X86 = {
    elsim.FILTER_ELEMENT_METH: filter_element_meth_basic,
    elsim.FILTER_CHECKSUM_METH: filter_checksum_meth_basic,
    elsim.FILTER_SIM_METH: filter_sim_meth_basic,
    elsim.FILTER_SORT_METH: filter_sort_meth_basic,
    elsim.FILTER_SKIPPED_METH: FilterNone,
}


class ProxyX86IDA(object):
    def __init__(self, ipipe):
        self.functions = ipipe.get_quick_functions()

    def get_elements(self):
        for i in self.functions:
            yield self.functions[i]
