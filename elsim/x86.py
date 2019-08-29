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

import elsim
from elsim.filters import FilterNone, filter_sort_meth_basic


class CheckSumFunc:
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



class Instruction:
    def __init__(self, i):
        self.mnemonic = i[1]

    def get_mnemonic(self):
        return self.mnemonic


class Function:
    def __init__(self, el, sim):
        self.function = el
        self.sim = sim
        self.__hash = None
        self.__checksum = None

    def get_instructions(self):
        for i in self.function.get_instructions():
            yield Instruction(i)

    def get_nb_instructions(self):
        return len(self.function.get_instructions())

    def __str__(self):
        return self.function.name

    @property
    def checksum(self):
        if not self.__checksum:
            self.__checksum = CheckSumFunc(self, self.sim)
        return self.__checksum

    @property
    def hash(self):
        if not self.__hash:
            self.__hash = mmh3.hash128(self.checksum.get_buff())
        return self.__hash


FILTERS_X86 = {
        elsim.FILTER_ELEMENT_METH: lambda element, iterable, sim: Function(element, sim),
        elsim.FILTER_SIM_METH: lambda sim, m1, m2: sim.ncd(m1.checksum.get_buff(), m2.checksum.get_buff()),
        elsim.FILTER_SORT_METH: filter_sort_meth_basic,
        elsim.FILTER_SKIPPED_METH: FilterNone,
}


class ProxyX86IDA(object):
    def __init__(self, ipipe):
        # FIXME: Not sure how this was used, but it was probably idapython?!
        self.functions = ipipe.get_quick_functions()

    def __iter__(self):
        yield from self.functions
