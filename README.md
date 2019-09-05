Elsim
=====

The elsim (ELement SIMilarity) library provides python functions to assess the similarity of byte strings
by using NCD (normalized compression distance).
While the library itself is not limited to comparision of any byte sequence, many tools
are specifically crafted to compare Android applications in the form of APK or DEX files.
In order to implement a new method for comparing objects of choice, a wrapper and some
weird filter dicts are used to put the data into the Elsim module.

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
would depend on Signature are moved to Signature itself (`get_method_signature()`).

History
-------

Elsim was first uploaded as a standalone library to code.google.com in March 2012. 
There is a [publication](http://phrack.org/issues/68/15.html) in the phrack magazine about Elsim from April 2012.
In September 2014, Elsim was added to the Androguard git repo but removed in 2017 with the
[big cleanup commit](https://github.com/androguard/androguard/commit/27a07fb4e0bbacd9229f76bb4ef76e7c119394aa).
Since then Androguard has changed significantly. Finally Elsim was resurrected in 2019.

Contributions
-------------

Ordered by Date:

* Anthony Desnos (2012 - 2015)
* Lircyn (2014)
* Robert Grosse (2014)
* Nikoli (2015)
* Subho Halder (2015)
* Sebastian Bachmann (2017, 2019)


Building
--------

Right now, no tests were conducted to make elsim work on Windows.
It was only tested on Linux (Debian Stretch).
To build elsim, you need some additional packages installed first:

`apt install build-essential liblzma-dev lzma-dev libmuparser-dev libsnappy-dev libbz2-dev zlib1g-dev libsparsehash-dev`

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
* removed simhash module from elsim codebase, as it is in pypi
* `elsim/db` was unified and many methods which seems to be never used and seems to were broken anyways were removed

Broken and not (yet) fixed
--------------------------

* Elsign
* unit tests for all the modules

Things that need design re-considerations
-----------------------------------------

currently there are two objects used to store the elements.
The first is a wrapper for the original element, the second a wrapper for the modified one.
This should somehow be replaced and all the lookups in the dicts can be enhanced as well.

The whole FILTER technique seems to be a neat idea but it is a PITA to implement.
Maybe it would be better to simply have to implement some class which has the required methods
and also provides the compareable types. Someone should think about a good solution here.

It might not be required to have all the compression methods as separate C libraries.
Many of the used compression libraries are already in the python's standard library.
These are for example `lzma`, `zlib` and `bz2`.
The question is also how much faster is the C code in reality.

The androdb tool seems to be a nice idea but it probably needs more work.
Also the database interface seems to be too complicated. One should consider writing another database
interface in SQL or another better database than the complicated dict madness.
It is also not quite clear what the intention was and how it _should_ work, as there were many
functions completely broken.

The native elsign module depends on the similarity module which makes it super hard to build it with python only.
This should be looked at and properly implemented, so that you dont need a ton of files
to compile for elsign but only the elsign module ifself.

There is an implementation of Bennett Complexity (Logical Depth).
But it is flawed, as it works only with certain compressors.
It is also questionable where this implementation comes from.

There is an implementation of CMID, where it also questionable for what
is shall be used and of it produces correct results. CMID seems to be
a very unfamiliar distance measure which is only used in one thesis
which is in french unfortunately.

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


The thing with NCD
------------------

NCD is not a fixed value but just an approximation, which heavily depends
on the compression method.
The problem with NCD is, that is solely uses the lengths of the compressed
strings and gives no answer to how similar two strings are in terms of
semantic.
Furthermore, all tested compression algorithms fail at the idempotency test.
They might be close but there is not a single observed case where it holds true.
If you think about it, it actually must be the case, as all tested compression
algorithms are loss-less, hence the information that the string is two times
the first string, must be coded somewhere. One exception might be compression
algorithms using fixed size length fields.

But, if the property of idempotency is not given, NCD can never be zero
as |C(xx)| > |C(x)|.
This means again, that the NCD measure will always overestimate the distance.

**FIXME: Further Research Required**

A solution to this problem seems to be the thresholding of values inside Elsim.
Right now, the threshold is set to be 0.2, which is very close to results we got
from testing two equal random strings with NCD.

Yet another question regards the compression method.
As we know, no compression method is able to fulfill the idempotecy property,
but we can get close.
The test is to take some strings we expect to work with and calculate both |C(x)| and |C(xx)|.
Next, we calculate the ratio of the two, namely |C(xx)| / |C(x)|.
This ratio will always be larger than 1, but the closer it is by one, better the compression method is.
A test using some APK files and calculating it for all strings as well as all methods using the Signature method
leads the following results (Numbers give `Mean(StdDeviation)`):

    String Compression (n = 1907)
                        |C(xx)|/|C(x)|     Time [ms]
    BZ2             @2: 1.0881(0.0398) ... 0.0245(0.0221)
    BZ2             @7: 1.0881(0.0398) ... 0.0199(0.0204)
    BZ2             @4: 1.0881(0.0398) ... 0.0221(0.0207)
    BZ2             @5: 1.0881(0.0398) ... 0.0210(0.0203)
    BZ2             @1: 1.0881(0.0398) ... 0.0351(0.0244)
    BZ2             @8: 1.0881(0.0398) ... 0.0192(0.0198)
    BZ2             @3: 1.0881(0.0398) ... 0.0226(0.0210)
    BZ2             @6: 1.0881(0.0398) ... 0.0202(0.0204)
    BZ2             @9: 1.0881(0.0398) ... 0.0190(0.0197)
    LZMA            @9: 1.1034(0.0575) ... 55.0540(0.5760)
    LZMA            @7: 1.1034(0.0575) ... 55.0250(0.5629)
    LZMA            @5: 1.1034(0.0575) ... 27.6373(0.4694)
    LZMA            @8: 1.1034(0.0575) ... 55.0339(0.5810)
    LZMA            @6: 1.1034(0.0575) ... 55.0691(0.5459)
    LZMA            @2: 1.1054(0.0594) ... 0.2580(0.0143)
    LZMA            @3: 1.1054(0.0594) ... 0.6889(0.0338)
    LZMA            @1: 1.1054(0.0594) ... 0.1991(0.0121)
    LZMA            @4: 1.1054(0.0594) ... 2.4724(0.1216)
    ZLIB            @7: 1.1111(0.0398) ... 0.0117(0.0030)
    ZLIB            @8: 1.1111(0.0398) ... 0.0116(0.0032)
    ZLIB            @9: 1.1111(0.0398) ... 0.0119(0.0036)
    ZLIB            @5: 1.1111(0.0398) ... 0.0119(0.0030)
    ZLIB            @6: 1.1111(0.0398) ... 0.0117(0.0029)
    ZLIB            @4: 1.1111(0.0398) ... 0.0125(0.0027)
    ZLIB            @3: 1.1112(0.0397) ... 0.0123(0.0025)
    ZLIB            @2: 1.1112(0.0397) ... 0.0136(0.0029)
    ZLIB            @1: 1.1113(0.0397) ... 0.0335(0.0047)
    XZ              @9: 1.1267(0.0501) ... 0.3989(0.1575)
    VCBLOCKSORT     @9: 1.3474(0.0480) ... 0.0386(0.0202)
    SNAPPY          @9: 1.3857(0.3389) ... 0.0062(0.0014)
    SMAZ            @9: 1.9709(0.0806) ... 0.0065(0.0052)

    Method compression (n = 10653)
    BZ2             @2: 1.0881(0.0398) ... 0.0245(0.0221)
    BZ2             @7: 1.0881(0.0398) ... 0.0199(0.0204)
    BZ2             @4: 1.0881(0.0398) ... 0.0221(0.0207)
    BZ2             @5: 1.0881(0.0398) ... 0.0210(0.0203)
    BZ2             @1: 1.0881(0.0398) ... 0.0351(0.0244)
    BZ2             @8: 1.0881(0.0398) ... 0.0192(0.0198)
    BZ2             @3: 1.0881(0.0398) ... 0.0226(0.0210)
    BZ2             @6: 1.0881(0.0398) ... 0.0202(0.0204)
    BZ2             @9: 1.0881(0.0398) ... 0.0190(0.0197)
    LZMA            @9: 1.1034(0.0575) ... 55.0540(0.5760)
    LZMA            @7: 1.1034(0.0575) ... 55.0250(0.5629)
    LZMA            @5: 1.1034(0.0575) ... 27.6373(0.4694)
    LZMA            @8: 1.1034(0.0575) ... 55.0339(0.5810)
    LZMA            @6: 1.1034(0.0575) ... 55.0691(0.5459)
    LZMA            @2: 1.1054(0.0594) ... 0.2580(0.0143)
    LZMA            @3: 1.1054(0.0594) ... 0.6889(0.0338)
    LZMA            @1: 1.1054(0.0594) ... 0.1991(0.0121)
    LZMA            @4: 1.1054(0.0594) ... 2.4724(0.1216)
    ZLIB            @7: 1.1111(0.0398) ... 0.0117(0.0030)
    ZLIB            @8: 1.1111(0.0398) ... 0.0116(0.0032)
    ZLIB            @9: 1.1111(0.0398) ... 0.0119(0.0036)
    ZLIB            @5: 1.1111(0.0398) ... 0.0119(0.0030)
    ZLIB            @6: 1.1111(0.0398) ... 0.0117(0.0029)
    ZLIB            @4: 1.1111(0.0398) ... 0.0125(0.0027)
    ZLIB            @3: 1.1112(0.0397) ... 0.0123(0.0025)
    ZLIB            @2: 1.1112(0.0397) ... 0.0136(0.0029)
    ZLIB            @1: 1.1113(0.0397) ... 0.0335(0.0047)
    XZ              @9: 1.1267(0.0501) ... 0.3989(0.1575)
    VCBLOCKSORT     @9: 1.3474(0.0480) ... 0.0386(0.0202)
    SNAPPY          @9: 1.3857(0.3389) ... 0.0062(0.0014)
    SMAZ            @9: 1.9709(0.0806) ... 0.0065(0.0052)


The results might lead to the opinion that the compression algorithms SMAZ, SNAPPY and VCBLOCKSORT are quite useless.
The best performing methods are BZ2 and LZMA.
SNAPPY which was used as the default compression method in the old papers seems to be not very good.
Moreover, it looks like the compression level for BZ2 and ZLIB does not really matter.
One reason might be that BZ2 and ZLIB are block-sorting algorithms, where the level just defines the windows size.
For example in BZ2, the level gives the window size in 100k blocks, hence the results just show that we never
had any inputs larger than 100k length.
For LZMA the compression level makes some difference but for levels larger than 4, the compression is very slow compared to the other methods.
The data would suggest that the best method (in terms of idempotecy) would actually be BZ2 at compression level 2.
SNAPPY is maybe four times faster but has less accuracy.

Yet another unanswered question is, if idempotency is the only factor influencing the result.
It should not and also the other properties might matter. A quantitative analysis of all properties might be required to
find the best compression method.

It should also be mentioned, that Elsim does not check identical strings via a NCD of zero.
Rather an exact compare is used to identify identical strings, hence this problem might not
be as big as exaggerated here.
There is also a paper covering this problem:

Alfonseca, Cebrián, Ortega (2005): Common Pitfalls Using the Normalized Compression Distance: What to Watch Out for in a Compressor

It can also be seen that the distance is quite stable when it comes to simple changes:

    >>> s.ncd(b'hello', b'hello')  # The same string, in theory distance 0
    0.1538461595773697
    >>> s.ncd(b'hello', b'hallo')
    0.23076923191547394
    >>> s.ncd(b'hello', b'hgllo')
    0.23076923191547394
    >>> s.ncd(b'hello', b'hqllo')
    0.23076923191547394
    >>> s.ncd(b'hello', b'hbllo')
    0.23076923191547394


The Cesare/Xiang Signature
--------------------------

One core feature of the Dalvik comparison is the use of a special grammar to normalize bytecode.
The idea of this grammar is certainly to provide a better starting point for compression,
instead of passing the raw bytecode - which is by its properties usually very high in entropy.
A low entropy string can usually compressed very well.

One disadvantage of the method is, that only the structure of the bytecode is looked at
and the content is lost. There are signature methods to provide some semantic information
but it is not used for most of the cases.
That means, that two methods which are dissimilar in their function might be identical in their
structure.
This might not be a problem but would be an interesting topic on its own for further investigations.


Simhash based lookups
---------------------

`androdb.py` uses simhash to lookup similar entries instead of using a n times m matrix of entries
with NCD. This is actually similar to the method described by [quarkslab](https://blog.quarkslab.com/android-application-diffing-engine-overview.html).

Androdb might be very slow for large datasets though.


Projects used
-------------

elsim contains (parts of) the following open source projects:

* Wu Manber's Multi-Pattern Search Algorithm: Copyright (C) 2008, One Unified
* Aho Corasick implementation: Copyright (C) 2007, Tideway Systems Limited
* The C clustering library: Copyright (C) 2002, Michiel Jan Laurens de Hoon
* [(classic) libcomplearn](https://github.com/rudi-cilibrasi/classic-complearn) (vcblocksort): Copyright (C) 2008, Rudi Cilibrasi
* [LZMA](https://www.7-zip.org/sdk.html): Public Domain 2009, Igor Pavlov
* [SMAZ](https://github.com/antirez/smaz): Copyright (C) 2006, Salvatore Sanfilippo

Licence
-------

Elsim is released as LGPL (v3 or later).

