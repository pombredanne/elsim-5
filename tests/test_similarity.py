import unittest

from elsim.similarity import SIMILARITY, SIMILARITYNative, SIMILARITYPython


class SimilarityTestsNative(unittest.TestCase):
    def test_loading(self):
        s = SIMILARITY(native_lib=True)

        self.assertIsInstance(s, SIMILARITY)
        self.assertIsInstance(s.s, SIMILARITYNative)

    def test_entropy(self):
        s = SIMILARITY(native_lib=True)

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


class SimilarityTestsPython(unittest.TestCase):
    def test_loading(self):
        s = SIMILARITY(native_lib=False)

        self.assertIsInstance(s, SIMILARITY)
        self.assertIsInstance(s.s, SIMILARITYPython)

    def test_entropy(self):
        s = SIMILARITY(native_lib=False)

        self.assertAlmostEqual(s.entropy(b'aaaaaaaaaa'), 0.0)


class SimilarityTestsEqual(unittest.TestCase):
    def test_entropy(self):
        s1 = SIMILARITY(native_lib=True)
        s2 = SIMILARITY(native_lib=False)

        strings = [b'aaaaaaaaa', b'ababababab', b'hello world', b'\x00\x01\x02\xffsdfsdgdsgjsdlk', bytearray(range(0, 256))]

        for s in strings:
            self.assertAlmostEqual(s1.entropy(s), s2.entropy(s))

