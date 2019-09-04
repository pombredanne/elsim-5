Elsim
=====

The elsim (ELement SIMilarity) library provides python functions to assess the similarity of byte strings
by using NCD (normalized compression distance).

The elsim library was part of androguard but removed around the v2.0 release of androguard.
It was filter-branch'ed from the androguard repository and fixes were applied to make it work
with newer androguard versions.

This version of the library only works with python >= 3.5 and requires androguard >= 3.4.0!

In many cases it was very hard to resurrect certain functions.
They would not work with the old androguard versions and no documention on the intended use
could be found. In such cases, a desired functionality was assumed and documented.
There are also cases of functions which would return wrong results. This was fixed, if noticed,
but could lead to different results, if the new elsim is compared to an old version.
The entropy calculation, for example, would return wrong results before and was fixed in this version.

A lot of code was not used in the filter-branched state of the library and was simply removed.
I'm sorry, if your project depended on that code.

Elsim also required certain functions from androguard, especially the `sign` module.
This module was moved from androguard to elsim and also heavily refactored.
It uses now XREFs instead of TaintedAnalysis, which could result in different output.
Now, Signature is a wrapper for an Analysis object and functions from the old Analysis which
would depend on Signature are moved to Signature itself (`get_method_signature()`.


Building
--------

Right now, no tests were conducted to make elsim work on Windows.
It was only tested on Linux (Debian Stretch).
To build elsim, you need some additional packages installed first:

`apt install build-essential liblzma-dev libmuparser-dev libsnappy-dev libbz2-dev zlib1g-dev libsparsehash-dev`

then use the `setup.py` to build elsim:

    $ virtualenv -p python3 venv
    $ . ./venv/bin/activate
    $ pip install -e .

Changes to original library
---------------------------

* Elsim now only supports python 3
* Switched the input to all functions in `elsim.similarity.Similarity` to bytes instead of str
* Replaced SHA256 hashing by Murmurhash3 128bit, which should be faster
* Removed SimilarityPython and replaced cpython interface with proper python API
* Fixed broken entropy calculation
* Changed filter system in Elsim (will probably change some more)
* Renamed modules and moved them around
* removed simhash module, as it is in pypi
* `elsim/db` was unified and many methods which seems to be never used and seems to were broken anyways were removed

Broken and not (yet) fixed
--------------------------

* Elsign

Things that need design re-considerations
-----------------------------------------

currently there are two objects used to store the elements.
The first is a wrapper for the original element, the second a wrapper for the modified one.
This should somehow be replaced and all the lookups in the dicts can be enhanced as well.

It might not be required to have all the compression methods as separate C libraries.
Many of the used compression libraries are already in the python's standard library.
These are for example `lzma`, `zlib` and `bz2`.

Unfortunately, we have no idea what kind of algorithm `VCBLOCKSORT` is. It seems to only occur in elsim
and has no description.

The androdb tool seems to be a nice idea but it probably needs more work.
Also the database interface seems to be too complicated. One should consider writing another database
interface in SQL or another better database than the complicated dict madness.
It is also not quite clear what the intention was and how it _should_ work, as there were many
functions completely broken.

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
* [SMAZ](https://github.com/antirez/smaz): Copyright (2006) Salvatore Sanfilippo, released as BSD 3-Clause
