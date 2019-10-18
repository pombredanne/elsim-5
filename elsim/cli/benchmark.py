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
import itertools
import collections
from operator import itemgetter
import time
import random
import math
import sys

from androguard.misc import AnalyzeAPK
from androguard.core.androconf import show_logging
from tqdm import tqdm
import click

from elsim import similarity
from elsim.sign import Signature


TESTS_RANDOM_SIGN = [b"B[F1]",
                     b"B[G]",
                     b"B[I]B[RF1]B[F0S]B[IF1]B[]B[]B[S]B[SS]B[RF0]B[]B[SP0I]B[GP1]",
                     b"B[R]B[F1]",
                     b"B[]B[]B[IR]",
                     b"B[G]B[SGIGF0]B[RP1G]B[SP1I]B[SG]B[SSGP0]B[F1]B[P0SSGR]B[F1]B[SSSI]B[RF1P0R]B[GSP0RP0P0]B[GI]B[P1]B[I]B[GP1S]",
                     b"B[P0SP1G]B[S]B[SGP0R]B[RI]B[GRS]B[P0]B[GRI]B[I]B[RP0I]B[SGRF0P0]B[I]B[]B[GGSP0]B[P1RSS]B[]B[S]B[IF1GP0]B[IP0P0GP0P1]B[P0RRRF0]B[R]B[R]B[RRF1S]B[F0P1R]",
                     b"B[SP0IP0F0P1]B[GS]B[F1]B[RP0]B[IF0P1S]B[P1]",
                     b"B[P0GSGP1]B[R]B[RP1P0]B[F1SIIGF1]B[G]B[F0SP1IF0I]B[RF1F0SIP1SG]B[P1GF1]B[P1G]B[F1P1GIIIGF1]B[F0F1P1RG]B[F1SF1]B[F1SRSS]B[GP0]B[SP1]B[IIF1]B[GIRGR]B[IP1]B[GG]B[RIP1RF1GS]B[SS]B[SSIP0GSP1]B[GGIGSP1G]B[P1GIGSGGI]B[P0P1IGRSRR]B[P1P0GP1]B[P1F1GGGS]B[RR]B[SIF1]B[SR]B[RSI]B[IIRGF1]",
                     ]


def print_timing(func):
    """
    A decorator to print the time consumed by a function
    """
    def wrapper(*arg, **kwargs):
        t1 = time.time()
        res = func(*arg, **kwargs)
        t2 = time.time()
        return res + (t2 - t1, )
    return wrapper


@print_timing
def test_idempotency(n, x):
    """C(xx) = C(x)"""
    # actually not testing if empty string produces empty compression, but this should always be the case!
    s1 = n.compress(x + x)
    s2 = n.compress(x)
    return s1 == s2, s1 + s2


@print_timing
def test_monotonicity(n, x, y):
    """C(x) <= C(xy)"""
    s1 = n.compress(x)
    s2 = n.compress(x + y)
    return s1 <= s2, s1 + s2


@print_timing
def test_symmetry(n, x, y):
    """C(xy) = C(yx)"""
    s1 = n.compress(x + y)
    s2 = n.compress(y + x)
    return s1 == s2, s1 + s2


@print_timing
def test_distributivity(n, x, y, z):
    """C(xy) + C(z) <=  C(xz) + C(yz)"""
    s1 = n.compress(x + y) + n.compress(z)
    s2 = n.compress(x + z) + n.compress(y + z)
    return s1 <= s2, s1 + s2


def test_normal_compressor(n, data):
    """
    A compressor C is "normal" if the following properties (inequalities) are
    satisfied:

    1) Idempotency: C(xx) = C(x), and C(E) = 0, where E is the empty string.
    2) Monotonicity: C(xy) >= C(x).
    3) Symmetry: C(xy) = C(yx).
    4) Distributivity: C(xy) + C(z) <= C(xz) + C(yz).

    The condition that C(E) = 0 is never tested, but should be the case for all compression
    methods.

    You can read more about this in Cilibrasi and Vitanyi (2003): Clustering by compression,
    especially in Section 3.1.
    """
    res = collections.OrderedDict()

    r, cc, times = zip(*map(lambda x: test_idempotency(n, x), data))
    res["Idempotency"] = (sum(r), len(r), sum(cc), sum(times))

    r, cc, times = zip(*map(lambda x: test_monotonicity(n, *x), itertools.permutations(data, 2)))
    res["Monotonicity"] = (sum(r), len(r), sum(cc), sum(times))

    r, cc, times = zip(*map(lambda x: test_symmetry(n, *x), itertools.permutations(data, 2)))
    res["Symmetry"] = (sum(r), len(r), sum(cc), sum(times))

    r, cc, times = zip(*map(lambda x: test_distributivity(n, *x), itertools.permutations(data, 3)))
    res["Distributivity"] = (sum(r), len(r), sum(cc), sum(times))

    return res


def generate_random_data(seed=42):
    """
    Returns 9 strings (bytes) with a length of 100 byte each

    Set the seed to get the same results again
    """
    random.seed(seed)
    return [bytearray([random.randrange(0, 256) for _ in range(100)]) for _ in range(9)]


def test_idempotency_quant(mystr):
    s = similarity.Similarity()
    results = dict()
    for x in similarity.Compress:
        s.set_compress_type(x)
        if x in (similarity.Compress.BZ2, similarity.Compress.ZLIB, similarity.Compress.LZMA):
            levels = range(1, 10)
        else:
            levels = [9]

        for level in levels:
            s.set_level(level)

            tic = time.time() * 1000
            s1 = s.compress(mystr)
            if s1 <= 0:
                # bad string?!
                print("ERROR IN STRING ({}): '{}...'".format(s1, repr(mystr[:20])), file=sys.stderr)
                continue

            s2 = s.compress(mystr * 2)
            toc = time.time() * 1000
            results[(x, level)] = (s1, s2, (s2 - s1) / s1, s2 / s1, toc - tic)
    # get the compression method with the lowest ratio if s2 / s1
    return sorted(results.items(), key=lambda x: x[1][3])


def print_res(results):
    r = []
    for k, v in results.items():
        average = sum(map(itemgetter(3), v)) / len(v)
        std = math.sqrt(sum(map(lambda x: (x - average)**2, map(itemgetter(3), v))) / (len(v) - 1))

        average_time = sum(map(itemgetter(4), v)) / len(v)
        std_time = math.sqrt(sum(map(lambda x: (x - average_time)**2, map(itemgetter(4), v))) / (len(v) - 1))

        r.append((k[0].name, k[1], average, std, average_time, std_time))

    print("Returns the compression algorithms plus the average ratio of itempotency and average time in ms")
    for l in sorted(r, key=itemgetter(2)):
        print("{:15s} @{}: {:8.6f}({:8.6f}) ... {:8.6f}({:8.6f})".format(*l))



@click.group()
def cli():
    pass


@cli.command()
@click.argument('apk', nargs=-1)
def compression(apk):
    """
    Test idempotency on actual APK files and return a ranking of compression algorithms

    This might be very slow and take up to some hours per APK given!
    """
    show_logging()

    overall_results = collections.defaultdict(list)
    overall_results_strings = collections.defaultdict(list)

    if apk == ():
        # Run a test on random data
        for _ in tqdm(range(1000)):
            # Go way beyond the block size
            b = bytearray([random.randrange(0, 256) for _ in range(100000)])
            for k, v in test_idempotency_quant(b):
                overall_results[k].append(v)

        print("----> RESULTS FOR BINARY COMPRESSION")
        print_res(overall_results)
        return

    for f in apk:
        print("-->", f)
        _, _, dx = AnalyzeAPK(f)
        sdx = Signature(dx)

        for s in tqdm(list(dx.strings.keys())):
            if s == b'':
                continue
            for k, v in test_idempotency_quant(s):
                overall_results_strings[k].append(v)

        for m in tqdm(list(dx.find_methods(no_external=True))):
            realmethod = m.get_method()
            sig = sdx.get_method_signature(realmethod, predef_sign="L0_4").get_string()
            if sig == b'':
                continue
            for k, v in test_idempotency_quant(sig):
                overall_results[k].append(v)

    print("----> RESULTS FOR STRING COMPRESSION")
    print_res(overall_results_strings)

    print("----> RESULTS FOR METHOD COMPRESSION")
    print_res(overall_results)


@cli.command()
@click.option("--rand", is_flag=True, help="Test Random bytes instead of Signature strings")
@click.option("--level", type=click.IntRange(1,9), default=9, help="Compression Level", show_default=True)
def benchmark(rand, level):
    """
    Run compressor tests and benchmarks

    The compression level has only an effect on LZMA!
    """
    sim_module = similarity.Similarity()
    if rand:
        test_data = generate_random_data()
    else:
        test_data = TESTS_RANDOM_SIGN

    table_line = '  {:20s}   {:>4d}    {:>4d}   {:>8d}   {:>7.5f}'

    print("Testing compression properties")
    print()
    print("The following properties are tested:")
    print('  1) Idempotency: C(xx) = C(x)')
    print('  2) Monotonicity: C(xy) >= C(x)')
    print('  3) Symmetry: C(xy) = C(yx)')
    print('  4) Distributivity: C(xy) + C(z) <= C(xz) + C(yz)')
    print("A detailed description can be found here: https://arxiv.org/abs/cs/0312044")
    print()
    print("Original (cummulated) length of data: {} bytes".format(sum(map(len, test_data))))
    print("Compression Level: {}".format(level))
    print()
    print("Testcase                   OK   Tests   CompSize   Time   ")
    print("==========================================================")

    for compressor in similarity.Compress:
        sim_module.set_level(level)
        sim_module.set_compress_type(compressor)

        print("* {}".format(compressor.name))
        # TODO we could actually print a ranking of the best performing algorithm
        # TODO it would also be interesting to see the actual difference of the tests
        for t_name, t_results in test_normal_compressor(sim_module, test_data).items():
            print(table_line.format(t_name, *t_results))
        print()

    print()
    print()
    print("Legend:")
    print("OK       ... defines the number of sucessful tests (higher is better)")
    print("Tests    ... the total number of tests run for the property")
    print("CompSize ... the sum of all compressed strings in the tests (lower is better)")
    print("Time     ... the computation time required for the compression (lower is better)")


if __name__ == "__main__":
    cli()
