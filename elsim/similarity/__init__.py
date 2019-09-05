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
    # FIXME: some functions simply return -1 on error.
    # This should be fixed and a proper exception must be thrown!
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
        :rtype: int
        """
        return ls.compress(self.level, s1)

    def ncd(self, s1, s2):
        """
        Calculate Normalized Compression Distance (NCD)

        The value is a floating point number between 0 and 1.
        0 describes the lowest distance, while 1 describes a maximal distance.

        The input must not be empty.
        
        .. warning::
            two identical inputs might not compute a NCD of zero!
            The reason lies in the properties of the compressor used.
            It can not simply be assumed that |C(xx)| = |C(x)|, even though
            this should be one property for a normal compressor (Idempotency).
            For example, the String 'hello' compressed with ZLIB results in
            a compressed string of length 13. But compressing 'hellohello' just
            has a length of 15. Hence, the NCD will be (15 - 13) / 13 = 0.1538!

        In the tests, no compression algorithm has the property of idempotency,
        hence the NCD value which is calculated by this method will always
        underestimate. That means the distance will always be greater than the actual distance!

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

        .. warning::
            The same problem applies as to the NCD:
            The result will always be smaller than the actual similarity!
            Two equal strings will not have a similarity of 1.

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

        .. warning::
            There is not much information about this metric, hence it should
            be used with caution!

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
        :rtype: int
        """
        return ls.kolmogorov(self.level, s1)

    def bennett(self, s1):
        """
        Calculates the Logical Depth
        It seems to be based on the paper
        Bennett, Charles H.: Logical depth and physical complexity (1988)

        .. warning::
            This function only works with ZLIB and SNAPPY as compressor!
            All other compressors do not have a de-compress implementation!
            If you ever use the bennett function directly from libsimilarity,
            and use other compressors, you are likely to get some segfaults!

        The implementation takes the input string and compresses it
        with the given compression method.
        Than the time is measured how long the de-compression of the
        string takes. This is done a thousand times and the average
        value is returned.
        This time value has the unit "CPU cycles", as this measure
        is taken before and after de-compression.

        This not only means that the result might differ depending
        on the load of the machine, it will also return different
        results per CPU.

        .. warning::
            There is not much information about this metric, hence it should
            be used with caution!

        :param bytes s1: input string
        :rtype: float
        """
        # Prevent segfaults
        if self.ctype not in (Compress.ZLIB, Compress.SNAPPY):
            raise ValueError("Can not use logical depth estimator with "
                             "other compression type than ZLIB or SNAPPY!")

        return ls.bennett(self.level, s1)

    def entropy(self, s1):
        """
        Calculate the (classical) Shannon Entropy

        :param bytes s1: input
        :returns: Shannon Entropy, a real number between 0 and 8
        :rtype: float
        """
        # FIXME: use the cache again
        return ls.entropy(s1)

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
        Set the compression level, if compression supports it.
        The level works only with the following compression methods:

        * BZ2: 1 <= level <= 9
        * LZMA: 0 <= level <= 9
        * ZLIB: 0 <= level <= 9

        For all other compressor types, the level has simply no effect.
        
        Note, that for ZLIB, a compression level of 0 is equal to no compression
        and the data is just copied!
        For ZLIB -1 can be specified to use the default compression method.
        Both methods are not possible with this method, as we strictly enforce
        compression levels between 1 and 9.

        .. warning::
            There are no sanity checks here! Except that the value is enforced
            to be between 1 and 9 - this means you can not use the level 0 on LZMA and ZLIB.
            If you specify a illegal compression level for a method,
            the functions will silently fail!

            The default level is set to 9 in this class, which will cause very heavy CPU loads
            in the case of LZMA! If you are using LZMA, you should probably reduce the level
            to about 5 or 6.

        :param int level: compression level, 1 <= level <= 9
        """
        if not (1 <= level <= 9):
            raise ValueError("For your own safety, the compression level must be 1 <= level <= 9!")
        self.level = level

