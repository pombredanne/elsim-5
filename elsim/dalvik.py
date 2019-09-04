"""
This module encapsultes dalvik code for the use with elsim
"""
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

from androguard.core.bytecodes import dvm

from elsim import debug
import elsim
from elsim.filters import filter_sort_meth_basic, FilterNone
from elsim import sign


class FilterSkip:
    def __init__(self, size=1, regexp=None):
        # Minimal size of one should always be the case. We can not compare to empty strings.
        self.size = size
        self.regexp = regexp

    def skip(self, m):
        if m.get_length() < self.size:
            return True

        if self.regexp and re.match(self.regexp, m.m.get_class_name()):
            return True

        return False

    def set_regexp(self, e):
        self.regexp = e

    def set_size(self, e):
        """
        :param int e: the minimal size:
        """
        if e < 0:
            raise ValueError("size must be positive integer")
        self.size = e


FILTERS_DALVIK_SIM = {
    elsim.FILTER_ELEMENT_METH: lambda element, iterator, sim: Method(iterator.vmx, iterator.sig, element, sim),
    elsim.FILTER_SIM_METH: lambda sim, e1, e2: sim.ncd(e1.checksum.get_signature(), e2.checksum.get_signature()),
    elsim.FILTER_SORT_METH: filter_sort_meth_basic,
    elsim.FILTER_SKIPPED_METH: FilterSkip(),
}

FILTERS_DALVIK_SIM_STRING = {
        elsim.FILTER_ELEMENT_METH: lambda element, iterator, sim: StringVM(element, sim),
        elsim.FILTER_SIM_METH: lambda sim, e1, e2: sim.ncd(e1.checksum.get_buff(), e2.checksum.get_buff()),
    elsim.FILTER_SORT_METH: filter_sort_meth_basic,
    elsim.FILTER_SKIPPED_METH: FilterNone,
}

FILTERS_DALVIK_BB = {
    elsim.FILTER_ELEMENT_METH: lambda element, iterator, sim: BasicBlock(element, sim),
    elsim.FILTER_SIM_METH: lambda sim, e1, e2: sim.ncd(e1.checksum.get_buff(), e2.checksum.get_buff()),
    elsim.FILTER_SORT_METH: filter_sort_meth_basic,
    elsim.FILTER_SKIPPED_METH: FilterNone,
}


class CheckSumMeth:
    def __init__(self, m1, sim, use_bytecode=False):
        """
        :param Method m1:
        :param elsim.similarity.Similarity sim:
        :param bool use_bytecode: should the bytecode be used instead of Signature module
        """
        self.m1 = m1
        self.sim = sim

        self.buff = ""
        self.signature = None
        self.signature_entropy = None

        # This essentially creates a long string with
        # all the instructions as names plus their operands in
        # a human readable form
        for i in m1.m.get_instructions():
            self.buff += dvm.clean_name_instruction(i)
            self.buff += dvm.static_operand_instruction(i)

        self.buff = self.buff.encode('UTF-8')
        self.entropy = sim.entropy(self.buff)

        if use_bytecode:
            if self.m1.m.get_code():
                self.signature = self.m1.m.get_code().get_bc().get_insn()
                self.signature_entropy = self.sim.entropy(self.signature)
            else:
                self.signature = b''
                self.signature_entropy = 0.0
        else:
            self.signature = self.m1.sig.get_method_signature(self.m1.m, predef_sign=sign.PredefinedSignature.L0_4).get_string()
            self.signature_entropy = self.sim.entropy(self.signature)

    def get_signature(self):
        """
        The Signature proposed here is an Android Variant of
        Cesare and Xiang (2010): Classification of Malware Using Structured Control Flow
        
        You can also read about this in http://phrack.org/issues/68/15.html
        """
        return self.signature

    def get_signature_entropy(self):
        return self.signature_entropy

    def get_entropy(self):
        return self.entropy

    def get_buff(self):
        return self.buff


class CheckSumBB:
    def __init__(self, basic_block, sim):
        self.basic_block = basic_block
        self.buff = ""
        for i in self.basic_block.bb.get_instructions():
            self.buff += dvm.clean_name_instruction(i)
            self.buff += dvm.static_operand_instruction(i)

        self.buff = self.buff.encode('UTF-8')
        self.hash = mmh3.hash128(self.buff)

    def get_buff(self):
        return self.buff

    def get_hash(self):
        return self.hash


class Method:
    """
    This object is used to calculate the similarity to another EncodedMethod
    """
    def __init__(self, vmx, sig, m, sim):
        """

        :param androguard.core.analysis.analysis.Analysis vmx:
        :param androguard.core.bytecodes.dvm.EncodedMethod m:
        """
        self.m = m
        self.vmx = vmx
        self.sig = sig
        self.mx = vmx.get_method(m)
        self.sim = sim

        self.sort_h = []

        self.__hash = None
        self.__checksum = None

    def __str__(self):
        return "%s %s %s %d" % (self.m.get_class_name(), self.m.get_name(), self.m.get_descriptor(), self.m.get_length())

    def get_length(self):
        """Returns the length of the code of the method"""
        return self.m.get_length()

    @property
    def checksum(self):
        if not self.__checksum:
            self.__checksum = CheckSumMeth(self, self.sim)
        return self.__checksum

    @property
    def hash(self):
        if not self.__hash:
            self.__hash = mmh3.hash128(self.checksum.get_buff())
        return self.__hash


class BasicBlock:
    def __init__(self, bb, sim):
        self.bb = bb
        self.sim = sim
        self.__hash = None
        self.__checksum = None

    def set_checksum(self, fm):
        self.checksum = fm

    @property
    def checksum(self):
        if not self.__checksum:
            self.__checksum = CheckSumBB(self, self.sim)
        return self.__checksum

    @property
    def hash(self):
        if not self.__hash:
            self.__hash = mmh3.hash128(self.checksum.get_buff())
        return self.__hash

    def __str__(self):
        return self.bb.name

    def show(self):
        print(self.bb.name)


class StringVM:
    def __init__(self, el, sim):
        self.el = el
        self.sim = sim
        self.__hash = None
        self.__checksum = None

    def get_length(self):
        return len(self.el)

    @property
    def checksum(self):
        if not self.__checksum:
            self.__checksum = CheckSumString(self, self.sim)
        return self.__checksum

    @property
    def hash(self):
        if not self.__hash:
            self.__hash = mmh3.hash128(self.checksum.get_buff())
        return self.__hash

    def __str__(self):
        return repr(self.el)


class CheckSumString:
    def __init__(self, m1, sim):
        self.m1 = m1
        self.sim = sim

        self.buff = self.m1.el

    def get_buff(self):
        # The MUTF8String is actually bytes
        return self.buff


class ProxyDalvik:
    """
    A simple proxy which uses the methods for comparison
    """
    def __init__(self, vmx):
        """
        :param androgaurd.core.analysis.analysis.Analysis vmx:
        """
        self.vmx = vmx
        self.sig = sign.Signature(vmx)

    def __iter__(self):
        """
        yield many EncodedMethod
        """
        for x in self.vmx.get_methods():
            if not x.is_external():
                yield x.get_method()


class ProxyDalvikMethod:
    """A Proxy for BasicBlocks"""
    def __init__(self, el):
        """
        :param Method el:
        """
        self.el = el

    def __iter__(self):
        yield from self.el.mx.basic_blocks.get()


class ProxyDalvikString:
    def __init__(self, vmx):
        self.vmx = vmx

    def __iter__(self):
        for i in self.vmx.get_strings():
            yield i.get_value()


def LCS(X, Y):
    """Longest Common Subsequence"""
    m = len(X)
    n = len(Y)
    # An (m+1) times (n+1) matrix
    C = [[0] * (n+1) for i in range(m+1)]
    for i in range(1, m+1):
        for j in range(1, n+1):
            if X[i-1] == Y[j-1]:
                C[i][j] = C[i-1][j-1] + 1
            else:
                C[i][j] = max(C[i][j-1], C[i-1][j])
    return C


def getDiff(C, X, Y, i, j, a, r):
    if i > 0 and j > 0 and X[i-1] == Y[j-1]:
        getDiff(C, X, Y, i-1, j-1, a, r)
        debug(" " + "%02X" % ord(X[i-1]))
    else:
        if j > 0 and (i == 0 or C[i][j-1] >= C[i-1][j]):
            getDiff(C, X, Y, i, j-1, a, r)
            a.append((j-1, Y[j-1]))
            debug(" + " + "%02X" % ord(Y[j-1]))
        elif i > 0 and (j == 0 or C[i][j-1] < C[i-1][j]):
            getDiff(C, X, Y, i-1, j, a, r)
            r.append((i-1, X[i-1]))
            debug(" - " + "%02X" % ord(X[i-1]))


def toString(bb, hS, rS):
    map_x = {}
    S = ""

    idx = 0
    nb = 0
    for i in bb.get_instructions():
        ident = dvm.clean_name_instruction(i)
        ident += dvm.static_operand_instruction(i)

        if ident not in hS:
            hS[ident] = len(hS)
            rS[chr(hS[ident])] = ident

        S += chr(hS[ident])
        map_x[nb] = idx
        idx += i.get_length()
        nb += 1

    return S, map_x


class DiffInstruction:
    def __init__(self, bb, instruction):
        self.bb = bb

        self.pos_instruction = instruction[0]
        self.offset = instruction[1]
        self.ins = instruction[2]

    def show(self):
        print(hex(self.bb.bb.start + self.offset), self.pos_instruction,
              self.ins.get_name(), self.ins.show_buff(self.bb.bb.start + self.offset))


class DiffBasicBlock:
    def __init__(self, x, y, added, deleted):
        self.basic_block_x = x
        self.basic_block_y = y
        self.added = sorted(added, key=itemgetter(1))
        self.deleted = sorted(deleted, key=itemgetter(1))

    def get_added_elements(self):
        for i in self.added:
            yield DiffInstruction(self.basic_block_x, i)

    def get_deleted_elements(self):
        for i in self.deleted:
            yield DiffInstruction(self.basic_block_y, i)


def filter_diff_bb(x, y):
    final_add = []
    final_rm = []

    hS = {}
    rS = {}

    X, map_x = toString(x.bb, hS, rS)
    Y, map_y = toString(y.bb, hS, rS)

    debug("%s %d" % (repr(X), len(X)))
    debug("%s %d" % (repr(Y), len(Y)))

    m = len(X)
    n = len(Y)

    C = LCS(X, Y)
    a = []
    r = []

    getDiff(C, X, Y, m, n, a, r)
    debug(a)
    debug(r)

    debug("DEBUG ADD")
    for i in a:
        instructions = [j for j in y.bb.get_instructions()]
        debug(" \t %s %s %s" % (
            i[0], instructions[i[0]].get_name(), instructions[i[0]].get_output()))
        final_add.append((i[0], map_y[i[0]], instructions[i[0]]))

    debug("DEBUG REMOVE")
    for i in r:
        instructions = [j for j in x.bb.get_instructions()]
        debug(" \t %s %s %s" % (
            i[0], instructions[i[0]].get_name(), instructions[i[0]].get_output()))
        final_rm.append((i[0], map_x[i[0]], instructions[i[0]]))

    return DiffBasicBlock(y, x, final_add, final_rm)


FILTERS_DALVIK_DIFF_BB = {
    elsim.DIFF: filter_diff_bb,
}


class ProxyDalvikBasicBlock:
    """
    This is actually a proxy for a Elsim object
    and is given to the Eldiff object
    """
    def __init__(self, esim):
        self.esim = esim

    def __iter__(self):
        yield from self.esim.split_elements()


class DiffDalvikMethod:
    def __init__(self, m1, m2, els, eld):
        self.m1 = m1
        self.m2 = m2
        self.els = els
        self.eld = eld

    def get_info_method(self, m):
        return m.m.get_class_name(), m.m.get_name(), m.m.get_descriptor()

    def show(self):
        print("[", self.get_info_method(self.m1), "]",
              "<->", "[", self.get_info_method(self.m2), "]")

        self.eld.show()
        self.els.show()
        self._show_elements("NEW", self.els.get_new_elements())

    def _show_elements(self, info, elements):
        for i in elements:
            print(i.bb, hex(i.bb.get_start()), hex(i.bb.get_end()))
            idx = i.bb.get_start()
            for j in i.bb.get_instructions():
                print("\t" + info, hex(idx), end=' ')
                j.show(idx)
                print()
                idx += j.get_length()

        print("\n")

