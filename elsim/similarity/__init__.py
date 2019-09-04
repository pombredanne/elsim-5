"""
Similarity measure module

This module implements similarity and complexity measures
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
from enum import IntEnum
from elsim.similarity import libsimilarity as ls

# Alias
entropy = ls.entropy


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


class Similarity:
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
    def __init__(self, ctype=Compress.ZLIB, level=9):
        """

        :param Compress ctype: type of compressor to use
        :param int level: level of compression to apply
        """
        self.level = level
        self.ctype = ctype
        self.set_compress_type(self.ctype)

    def compress(self, s1):
        """
        Returns the length of the compressed string

        :param bytes s1: the string to compress
        """
        return ls.compress(self.level, s1)

    def ncd(self, s1, s2):
        """
        Calculate Normalized Compression Distance (NCD)

        The value is a floating point number between 0 and 1.
        0 describes the lowest distance, i.e. the two inputs are equal,
        while 1 describes a maximal distance.

        :param bytes s1: The first string
        :param bytes s2: The second string
        """
        # FIXME: use the cache again
        # there is a flaw in the old design, as it would use a single cache for all functions
        # hence, if you calculate ncd(s1, s2) and then ncs(s1, s2), you would get the result from
        # before!
        n, ls1, ls2 = ls.ncd(self.level, s1, s2)
        return n

    def ncs(self, s1, s2):
        """
        Calculate Normalized Compression Similarity
        which is defined as 1 - ncd(s1, s2).

        :param bytes s1: The first string
        :param bytes s2: The second string
        """
        # FIXME: use the cache again
        n, ls1, ls2 = ls.ncs(self.level, s1, s2)
        return n

    def cmid(self, s1, s2):
        """
        Calculate Compresson based Mutual Inclusion Degree

        It seems this is a implementation of CMID which is explained in:
        Borello, Jean-Marie: Étude du métamorphisme viral: modélisation, conception et détection (2011)

        :param bytes s1: The first string
        :param bytes s2: The second string
        """
        # FIXME: use the cache again
        n, ls1, ls2 = ls.cmid(self.level, s1, s2)
        return n

    def kolmogorov(self, s1):
        """
        Calculate an upper bound for the Kolmogorov Complexity
        using compression method.

        As the actual value of the Kolmogorov Complexity is not computable,
        this is just an approximate value, which will change based on the
        compression method used.

        :param bytes s1: input string
        """
        return ls.kolmogorov(self.level, s1)

    def bennett(self, s1):
        """
        Calculates the Logical Depth
        It seems to be based on the paper
        Bennett, Charles H.: Logical depth and physical complexity (1988)

        :param bytes s1: input string
        """
        return ls.bennett(self.level, s1)

    def entropy(self, s1):
        """
        Calculate the (classical) Shannon Entropy

        :param bytes s1: input
        """
        # FIXME: use the cache again
        return ls.entropy(s1)

    def RDTSC(self):
        """
        Returns the value in the Timestamp Counter
        which is a CPU register
        """
        return ls.RDTSC()

    def levenshtein(self, s1, s2):
        """
        Calculate Levenshtein distance

        :param bytes s1: The first string
        :param bytes s2: The second string
        """
        return ls.levenshtein(s1, s2)

    def set_compress_type(self, t):
        """"
        Set the type of compressor to use

        :param Compress t: the compression method
        """
        self.ctype = t
        ls.set_compress_type(t)

    def set_level(self, level):
        """
        Set the compression level, if compression supports it

        Usually this is an integer value between 0 and 9

        :param int level: compression level
        """
        self.level = level

