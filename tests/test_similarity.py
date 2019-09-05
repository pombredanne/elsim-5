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

from elsim.similarity import Similarity


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

