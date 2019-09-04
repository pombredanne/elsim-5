Elsim
=====

The elsim library works only with an old version of androguard, probably a pre v2.0 release.

It was filter-branch'ed from the androguard repository.

Building
--------

To build elsim, you need some additional packages:

`apt install build-essential liblzma-dev libmuparser-dev libsnappy-dev libbz2-dev zlib1g-dev libsparsehash-dev`

then use the makefile to build elsim:

`make`

For running elsim, those packages should be sufficant:

`apt install python libstdc++6 libgcc1 lib6 liblzma5 libmuparser2v5 libsnappy1v5 libbz2-1.0 zlib1g`

Changes to original library
---------------------------

* Replaced SHA256 hashing by Murmurhash3 128bit
* Removed SimilarityPython
* Fixed broken entropy calculation
* Changed Filter System in Elsim
* Renamed modules and moved them around

Things that need design re-considerations
-----------------------------------------

currently there are two objects used to store the elements.
The first is a wrapper for the original element, the second a wrapper for the modified one.
This should somehow be replaced and all the lookups in the dicts can be enhanced as well.

Compression Method
------------------

The original publication had a benchmark included, which compression method
is the best. Usually you will choose the fastest compression method, which gives the best
results in NCD.
The original publication found, that SNAPPY has these properties.
You can use the `benchmark.py` script to test all available compressors
for the "normal compressor" property and compression times.

But from the benchmarks, you can also see that BZ2 performs very well.
The compressor to use probably also depends on the data used.
This was not investigated yet.

Here is a quick demo using the fdroid client in two similar versions:

    $ for x in SNAPPY BZ2 ZLIB XZ VCBLOCKSORT SMAZ LZMA; do echo $x; time python dalviksim.py --compressor $x --score org.fdroid.fdroid_10.apk org.fdroid.fdroid_12.apk --xstrings --deleted --new; echo ""; done
    SNAPPY
    Methods: 86.9526
    Strings: 89.5279
    real    0m1.289s
    user    0m1.312s
    sys     0m0.208s

    BZ2
    Methods: 90.3301
    Strings: 90.9782
    real    0m1.772s
    user    0m1.776s
    sys     0m0.228s

    ZLIB
    Methods: 91.7040
    Strings: 90.5723
    real    0m1.280s
    user    0m1.288s
    sys     0m0.224s

    XZ
    Methods: 93.4123
    Strings: 92.0139
    real    0m3.514s
    user    0m2.544s
    sys     0m1.124s

    VCBLOCKSORT
    Methods: 85.8525
    Strings: 87.7660
    real    0m1.673s
    user    0m1.708s
    sys     0m0.196s

    SMAZ
    Methods: 75.0000
    Strings: 85.4922
    real    0m1.324s
    user    0m1.332s
    sys     0m0.228s

    LZMA
    Methods: 92.7481
    Strings: 90.5851
    real    1m2.146s
    user    0m29.160s
    sys     0m33.204s

From that output, I would always use XZ as it gives the highest similarity.
This test should be performed again with two APKs which are different in a defined number of items to investigate the changes correctly!


Projects used
-------------

elsim contains (parts of) the following open source projects:

* Wu Manber's Multi-Pattern Search Algorithm: Copyright (2008) One Unified
* Aho Corasick implementation: Copyright (2007) Tideway Systems Limited
* The C clustering library: Copyright (2002) Michiel Jan Laurens de Hoon
* LZMA: Public Domain (2009) Igor Pavlov
