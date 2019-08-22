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
import zlib
import bz2
import math
import json
import re
from enum import IntEnum
from elsim.similarity import libsimilarity as ls


def entropy(data):
    """
    Return Shannon entropy for bytes

    :param bytes data: input
    """
    H = 0.0

    if len(data) == 0:
        return H

    for x in range(256):
        p_x = float(data.count(x))/len(data)
        if p_x > 0:
            H += - p_x*math.log(p_x, 2)

    return H


class Compress(IntEnum):
    """Enum for the compression type"""
    ZLIB = 0
    BZ2 = 1
    SMAZ = 2
    LZMA = 3
    XZ = 4
    SNAPPY = 5
    VCBLOCKSORT = 6

    @staticmethod
    def by_name(name):
        """Get attributes by name instead of integer"""
        if hasattr(Compress, name):
            return getattr(Compress, name)
        raise ValueError("Compression method '{}' was not found!".format(name))


class SIMILARITYBase:
    def __init__(self):
        self.ctype = Compress.ZLIB

        self.__caches = {k: dict() for k in Compress}
        self.__rcaches = {k: dict() for k in Compress}
        self.__ecaches = dict()

        self.level = 9

    def set_level(self, level):
        self.level = level

    def get_in_caches(self, s):
        try:
            return self.__caches[self.ctype][zlib.adler32(s)]
        except KeyError:
            return 0

    def get_in_rcaches(self, s1, s2):
        try:
            return self.__rcaches[self.ctype][zlib.adler32(s1 + s2)]
        except KeyError:
            try:
                return self.__rcaches[self.ctype][zlib.adler32(s2 + s1)]
            except KeyError:
                return -1, -1

    def add_in_caches(self, s, v):
        h = zlib.adler32(s)
        if h not in self.__caches[self.ctype]:
            self.__caches[self.ctype][h] = v

    def add_in_rcaches(self, s, v):
        h = zlib.adler32(s)
        if h not in self.__rcaches[self.ctype]:
            self.__rcaches[self.ctype][h] = v

    def clear_caches(self):
        for i in self.__caches:
            self.__caches[i] = {}

    def add_in_ecaches(self, s, v, r):
        h = zlib.adler32(s)
        if h not in self.__ecaches:
            self.__ecaches[h] = (v, r)

    def get_in_ecaches(self, s1):
        try:
            return self.__ecaches[zlib.adler32(s1)]
        except KeyError:
            return -1, -1

    def __nb_caches(self, caches):
        nb = 0
        for i in caches:
            nb += len(caches[i])
        return nb

    def set_compress_type(self, t):
        self.ctype = t

    def show(self):
        print("ECACHES", len(self.__ecaches))
        print("RCACHES", self.__nb_caches(self.__rcaches))
        print("CACHES", self.__nb_caches(self.__caches))


class SIMILARITYNative(SIMILARITYBase):
    def __init__(self):
        super().__init__()
        self.set_compress_type(self.ctype)

    def compress(self, s1):
        return ls.compress(self.level, s1)

    def ncd(self, s1, s2):
        # FIXME: use the cache again
        # there is a flaw in the old design, as it would use a single cache for all functions
        # hence, if you calculate ncd(s1, s2) and then ncs(s1, s2), you would get the result from
        # before!
        return ls.ncd(self.level, s1, s2)

    def ncs(self, s1, s2):
        # FIXME: use the cache again
        return ls.ncs(self.level, s1, s2)

    def cmid(self, s1, s2):
        # FIXME: use the cache again
        return ls.cmid(self.level, s1, s2)

    def kolmogorov(self, s1):
        return ls.kolmogorov(self.level, s1)

    def bennett(self, s1):
        return ls.bennett(self.level, s1)

    def entropy(self, s1):
        # FIXME: use the cache again
        return ls.entropy(s1)

    def RDTSC(self):
        return ls.RDTSC()

    def levenshtein(self, s1, s2):
        return ls.levenshtein(s1, s2)

    def set_compress_type(self, t):
        super().set_compress_type(t)
        ls.set_compress_type(t)


class SIMILARITYPython(SIMILARITYBase):
    def __init__(self):
        super(SIMILARITYPython, self).__init__()

    def set_compress_type(self, t):
        self.ctype = t
        if self.ctype not in (Compress.ZLIB, Compress.BZ2):
            print(
                "warning: compressor %s is not supported by python method (using ZLIB as fallback)" % t.name)
            self.ctype = Compress.ZLIB

    def compress(self, s1):
        return len(self._compress(s1))

    def _compress(self, s1):
        if self.ctype == Compress.ZLIB:
            return zlib.compress(s1, self.level)
        if self.ctype == Compress.BZ2:
            return bz2.compress(s1, self.level)

    def _sim(self, s1, s2, func):
        end = self.get_in_rcaches(s1, s2)
        if end != -1:
            return end

        corig = self.get_in_caches(s1)
        ccmp = self.get_in_caches(s2)

        res, corig, ccmp = func(s1, s2, corig, ccmp)

        self.add_in_caches(s1, corig)
        self.add_in_caches(s2, ccmp)
        self.add_in_rcaches(s1+s2, res)

        return res

    def _ncd(self, s1, s2, s1size=0, s2size=0):
        if s1size == 0:
            s1size = self.compress(s1)

        if s2size == 0:
            s2size = self.compress(s2)

        s3size = self.compress(s1+s2)

        smax = max(s1size, s2size)
        smin = min(s1size, s2size)

        res = (abs(s3size - smin)) / float(smax)
        if res > 1.0:
            res = 1.0

        return res, s1size, s2size

    def ncd(self, s1, s2):
        return self._sim(s1, s2, self._ncd)

    def ncs(self, s1, s2):
        ncd, l1, l2 = self.ncd(s1, s2)
        return 1.0 - ncd, l1, l2

    def entropy(self, s1):
        end, ret = self.get_in_ecaches(s1)
        if end != -1:
            return end, ret

        res = entropy(s1)
        self.add_in_ecaches(s1, res, 0)

        return res

    def levenshtein(self, a, b):
        n, m = len(a), len(b)
        if n > m:
            # Make sure n <= m, to use O(min(n,m)) space
            a, b = b, a
            n, m = m, n

        current = range(n + 1)
        for i in range(1, m + 1):
            previous, current = current, [i]+[0]*n
            for j in range(1, n + 1):
                add, delete = previous[j]+1, current[j-1]+1
                change = previous[j-1]
                if a[j-1] != b[i-1]:
                    change = change + 1
                current[j] = min(add, delete, change)

        return current[n]


class SIMILARITY:
    """
    The Similarity class capsules all important functions for calculating
    similarities.

    The whole class works always with bytes!
    Therefore it is required to encode strings using an appropriate encoding scheme.
    If str are supplied, they will automatically get encoded using UTF-8.

    To increase the computation speed, all inputs to methods of this class
    are cached. Adler32 hash is used as a key for checking the cache.
    This means, that there is a slight decrease in speed when using only
    a few items, but there should be an increase if a reasonable number
    of strings is compared.

    """

    def __init__(self, native_lib=True):
        """

        :param bool native_lib: True of native lib should be used or False for pure python version
        """
        if native_lib:
            try:
                self.s = SIMILARITYNative()
            except Exception as e:
                print(e)
                self.s = SIMILARITYPython()
        else:
            self.s = SIMILARITYPython()

    def set_level(self, level):
        """
        Set the compression level, if compression supports it

        Usually this is an integer value between 0 and 9

        :param int level: compression level
        """
        return self.s.set_level(level)

    def set_compress_type(self, t):
        """"
        Set the type of compressor to use

        :param Compress t: the compression method
        """
        return self.s.set_compress_type(t)

    @staticmethod
    def _encode(s):
        """Checks if bytes or encode with UTF-8"""
        if isinstance(s, bytes):
            return s
        return s.encode('UTF-8')

    def compress(self, s1):
        """
        Returns the length of the compressed string

        :param bytes s1: the string to compress
        """
        return self.s.compress(self._encode(s1))

    def ncd(self, s1, s2):
        """
        Calculate Normalized Compression Distance (NCD)

        The value is a floating point number between 0 and 1.
        0 describes the lowest distance, i.e. the two inputs are equal,
        while 1 describes a maximal distance.

        :param bytes s1: The first string
        :param bytes s2: The second string
        """
        return self.s.ncd(self._encode(s1), self._encode(s2))[0]

    def ncs(self, s1, s2):
        """
        Calculate Normalized Compression Similarity
        which is defined as 1 - ncd(s1, s2).

        :param bytes s1: The first string
        :param bytes s2: The second string
        """
        return self.s.ncs(self._encode(s1), self._encode(s2))[0]

    def cmid(self, s1, s2):
        """
        Calculate Compresson based Mutual Inclusion Degree

        It seems this is a implementation of CMID which is explained in:
        Borello, Jean-Marie: Étude du métamorphisme viral: modélisation, conception et détection (2011)

        :param bytes s1: The first string
        :param bytes s2: The second string
        """
        return self.s.cmid(self._encode(s1), self._encode(s2))[0]

    def kolmogorov(self, s1):
        """
        Calculate an upper bound for the Kolmogorov Complexity
        using compression method.

        As the actual value of the Kolmogorov Complexity is not computable,
        this is just an approximate value, which will change based on the
        compression method used.

        :param bytes s1: input string
        """
        return self.s.kolmogorov(self._encode(s1))

    def bennett(self, s1):
        """
        Calculates the Logical Depth
        It seems to be based on the paper
        Bennett, Charles H.: Logical depth and physical complexity (1988)

        :param bytes s1: input string
        """
        return self.s.bennett(self._encode(s1))

    def entropy(self, s1):
        """
        Calculate the (classical) Shannon Entropy

        :param bytes s1: input
        """
        return self.s.entropy(self._encode(s1))

    def RDTSC(self):
        """
        Returns the value in the Timestamp Counter
        which is a CPU register
        """
        return self.s.RDTSC()

    def levenshtein(self, s1, s2):
        """
        Calculate Levenshtein distance

        :param bytes s1: The first string
        :param bytes s2: The second string
        """
        return self.s.levenshtein(self._encode(s1), self._encode(s2))

    def show(self):
        self.s.show()


class DBFormat(object):
    def __init__(self, filename):
        self.filename = filename

        self.D = {}

        fd = None

        try:
            with open(self.filename, "r+") as fd:
                self.D = json.load(fd)
        except IOError:
            print("Impossible to open filename: " + filename)
            self.D = {}

        self.H = {}
        self.N = {}

        for i in self.D:
            self.H[i] = {}
            for j in self.D[i]:
                if j == "NAME":
                    self.N[i] = re.compile(self.D[i][j])
                    continue

                self.H[i][j] = {}
                for k in self.D[i][j]:
                    if isinstance(self.D[i][j][k], dict):
                        self.H[i][j][k] = set()
                        for e in self.D[i][j][k].keys():
                            self.H[i][j][k].add(long(e))

    def add_name(self, name, value):
        if name not in self.D:
            self.D[name] = {}

        self.D[name]["NAME"] = value

    def add_element(self, name, sname, sclass, size, elem):
        try:
            if elem not in self.D[name][sname][sclass]:
                self.D[name][sname][sclass][elem] = size
                self.D[name][sname]["SIZE"] += size

        except KeyError:
            if name not in self.D:
                self.D[name] = {}
                self.D[name][sname] = {}
                self.D[name][sname]["SIZE"] = 0
                self.D[name][sname][sclass] = {}
            elif sname not in self.D[name]:
                self.D[name][sname] = {}
                self.D[name][sname]["SIZE"] = 0
                self.D[name][sname][sclass] = {}
            elif sclass not in self.D[name][sname]:
                self.D[name][sname][sclass] = {}

            self.D[name][sname]["SIZE"] += size
            self.D[name][sname][sclass][elem] = size

    def is_present(self, elem):
        for i in self.D:
            if elem in self.D[i]:
                return True, i
        return False, None

    def elems_are_presents(self, elems):
        ret = {}
        info = {}

        for i in self.H:
            ret[i] = {}
            info[i] = {}

            for j in self.H[i]:
                ret[i][j] = {}
                info[i][j] = {}

                for k in self.H[i][j]:
                    val = [self.H[i][j][k].intersection(
                        elems), len(self.H[i][j][k]), 0, 0]

                    size = 0
                    for z in val[0]:
                        size += self.D[i][j][k][str(z)]

                    val[2] = (float(len(val[0]))/(val[1])) * 100
                    val[3] = size

                    if val[3] != 0:
                        ret[i][j][k] = val

                info[i][j]["SIZE"] = self.D[i][j]["SIZE"]

        return ret, info

    def classes_are_presents(self, classes):
        m = set()
        for j in classes:
            for i in self.N:
                if self.N[i].search(j) != None:
                    m.add(i)
        return m

    def show(self):
        for i in self.D:
            print(i, ":")
            for j in self.D[i]:
                print("\t", j, len(self.D[i][j]))
                for k in self.D[i][j]:
                    print("\t\t", k, len(self.D[i][j][k]))

    def save(self):
        with open(self.filename, "w") as fd:
            json.dump(self.D, fd)
