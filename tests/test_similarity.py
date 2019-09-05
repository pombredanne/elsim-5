# This file is part of Elsim
#
# Copyright (C) 2019, Sebastian Bachmann <hello at reox.at>
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
import unittest

from elsim.similarity import Similarity, Compress


class SimilarityTestsNative(unittest.TestCase):
    def test_loading(self):
        s = Similarity()

        self.assertIsInstance(s, Similarity)

    def test_entropy(self):
        s = Similarity()

        self.assertAlmostEqual(s.entropy(b''), 0.0)
        self.assertAlmostEqual(s.entropy(b'aaaaaaaaaa'), 0.0)
        self.assertAlmostEqual(s.entropy(b'ababababab'), 1.0)
        self.assertAlmostEqual(s.entropy(b'bababababa'), 1.0)
        self.assertAlmostEqual(s.entropy(b'aaabbbccc'), 1.58496, places=5)
        self.assertAlmostEqual(s.entropy(b'hello world'), 2.84535, places=5)
        self.assertAlmostEqual(s.entropy(b'hello world2'), 3.02206, places=5)
        self.assertAlmostEqual(s.entropy(b'abcdefghijklmnopqrstuvwxyz'), 4.70044, places=5)
        self.assertAlmostEqual(s.entropy(bytearray(range(0, 256))), 8.0)
        self.assertAlmostEqual(s.entropy(bytearray(range(0, 256)) * 2), 8.0)
        self.assertAlmostEqual(s.entropy(bytearray(range(0, 256)) * 10), 8.0)
        self.assertAlmostEqual(s.entropy(bytearray(range(0, 128))), 7.0)
        self.assertAlmostEqual(s.entropy(bytearray(range(128, 256))), 7.0)
        self.assertAlmostEqual(s.entropy(bytearray(range(0, 256, 2))), 7.0)
        self.assertAlmostEqual(s.entropy(bytearray(range(0, 256, 2)) * 2), 7.0)

    def test_compression(self):
        """
        Test if compression works and we get some result
        """
        s = Similarity()

        for comp in Compress:
            s.set_compress_type(comp)

            if comp in (Compress.BZ2, Compress.ZLIB, Compress.LZMA):
                levels = range(1, 10)
            else:
                levels = [9]

            for level in levels:
                s.set_level(level)
                input_string = 'hello world -> {} / {}'.format(comp.name, level)
                res = s.compress(input_string.encode('ascii'))
                print(comp, level, res, len(input_string))
                self.assertTrue(res > 0)

        with self.assertRaises(ValueError):
            s.set_level(0)

        with self.assertRaises(ValueError):
            s.set_level(-1)

        with self.assertRaises(ValueError):
            s.set_level(10)

        with self.assertRaises(ValueError):
            s.set_level(9999)

    def test_levenshtein(self):
        """tests the levenshtein distance"""
        s = Similarity()

        self.assertEqual(s.levenshtein(b'hello', b'hello'), 0)
        self.assertEqual(s.levenshtein(b'hello', b'hallo'), 1)
        self.assertEqual(s.levenshtein(b'Tier', b'Tor'), 2)  # Wikipedia
        self.assertEqual(s.levenshtein(b'kitten', b'sitting'), 3)  # Wikipedia
        self.assertEqual(s.levenshtein(b'flaw', b'lawn'), 2)  # Wikipedia
        self.assertEqual(s.levenshtein(b'FLOMAX', b'VOLMAX'), 3)
        self.assertEqual(s.levenshtein(b'GILY', b'GEELY'), 2)
        self.assertEqual(s.levenshtein(b'HONDA', b'HYUNDAI'), 3)
        self.assertEqual(s.levenshtein(b'lsjdflksdjfkl', b'sdfljsdlkjglksdahglksdhgkls'), 17)

    def test_ncd(self):
        """tests if NCD/NCS are working"""
        s = Similarity()

        mystr = b'hello'

        for x in Compress:
            s.set_compress_type(x)
            if x in (Compress.BZ2, Compress.ZLIB, Compress.LZMA):
                levels = range(1, 10)
            else:
                levels = [9]

            for level in levels:
                s.set_level(level)

                s1 = s.compress(mystr)
                s2 = s.compress(mystr * 2)
                self.assertGreater(s1, 0)
                self.assertGreater(s2, 0)
                self.assertAlmostEqual(s.ncd(mystr, mystr), (s2 - s1) / s1)
                self.assertAlmostEqual(s.ncs(mystr, mystr), 1.0 - ((s2 - s1) / s1))

