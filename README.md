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

### BZ2

Uses the [bzip2](https://packages.debian.org/source/sid/bzip2) library, which must be installed externally, to compress data.
`workFactor` is fixed to 30, `level` is equal to the parameter `blockSize100k`.

### ZLIB

Uses the [zlib](https://packages.debian.org/source/sid/zlib), which must be installed externally, to compress data.
Uses the deflate mode and `level` can be set.

### LZMA

Uses the [LZMA SDK](https://www.7-zip.org/sdk.html), which is included in a version dated from 2008, to compress data.
All parameters like `dictSize`, `lc`, `lp`, `pb`, `fb` and `numThreads` are set to default,
`level` can be adjusted.

### XZ

Uses the [liblzma](https://packages.debian.org/source/sid/xz-utils), which must be installed externally, to compress data.
The preset it set to `COMPRESSION_LEVEL` = 9 and `EXTREME` compression,
integrity check is set to `LZMA_CHECK_NONE`.
The level can not be set.

### SNAPPY

Uses [libsnappy](https://packages.debian.org/source/sid/snappy), which must be installed externally, to compress data.
Snappy has no settings.

### VCBLOCKSORT

Uses a blocksort algorithm which was implemented in [libcomplearn](https://github.com/rudi-cilibrasi/classic-complearn) (classic variant).
It has no settings.

### SMAZ

Uses the [Short String compression](https://github.com/antirez/smaz) which is basically a codebook compression
method. SMAZ is not a general compressor but should only be used for strings
in the english language.
It has no settings.

### Benchmark

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

Size limits of Compression Method
---------------------------------

Apparently, there are limitations to the sizes you can pass to a compressor.
This only plays a role, if the compressed data is larger than the input data
and this size exceeds 1000k bytes.
Some compression algorithms handle this elegantly, others like SMAZ or SNAPPY will simply segfault.
It is safe to assume that generic inputs up to about 900k byte are safe from this.

Note, that this might lead to unwanted buffer overflows and exploitability.
Someone should fix this...


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

    APK = org.fdroid.fdroid_99250.apk (SHA256 d305a0f83430af7cc08bfd1fa9e02b4f569fa7d5ec57745e98fa13fd9fa2069e)

    String Compression (n = 9200)
                        |C(xx)|/|C(x)|     Time [ms]
    BZ2             @3: 1.093858(0.048214) ... 0.025234(0.021899)
    BZ2             @7: 1.093858(0.048214) ... 0.020992(0.020203)
    BZ2             @4: 1.093858(0.048214) ... 0.023719(0.021039)
    BZ2             @6: 1.093858(0.048214) ... 0.021661(0.020449)
    BZ2             @9: 1.093858(0.048214) ... 0.020121(0.020089)
    BZ2             @2: 1.093858(0.048214) ... 0.027183(0.023237)
    BZ2             @5: 1.093858(0.048214) ... 0.022673(0.020646)
    BZ2             @1: 1.093858(0.048214) ... 0.037637(0.026436)
    BZ2             @8: 1.093858(0.048214) ... 0.020514(0.020182)
    LZMA            @9: 1.101936(0.065057) ... 51.740248(0.178973)
    LZMA            @7: 1.101936(0.065057) ... 51.805637(0.417721)
    LZMA            @8: 1.101936(0.065057) ... 51.747647(0.304659)
    LZMA            @5: 1.102038(0.065313) ... 26.465008(0.296255)
    LZMA            @6: 1.102038(0.065313) ... 52.181474(0.262509)
    LZMA            @2: 1.102893(0.066298) ... 0.251180(0.009412)
    LZMA            @3: 1.102893(0.066298) ... 0.670779(0.016792)
    LZMA            @1: 1.102893(0.066298) ... 0.190088(0.011277)
    LZMA            @4: 1.102893(0.066298) ... 2.358383(0.042710)
    ZLIB            @8: 1.108001(0.043343) ... 0.011485(0.002943)
    ZLIB            @9: 1.108001(0.043343) ... 0.011607(0.003478)
    ZLIB            @7: 1.108024(0.043413) ... 0.011615(0.002817)
    ZLIB            @6: 1.108117(0.043588) ... 0.011722(0.004362)
    ZLIB            @5: 1.108357(0.044119) ... 0.011986(0.002920)
    ZLIB            @4: 1.108768(0.044694) ... 0.012678(0.003019)
    ZLIB            @3: 1.108986(0.044762) ... 0.012712(0.002875)
    ZLIB            @2: 1.109213(0.045376) ... 0.019638(0.004050)
    ZLIB            @1: 1.109308(0.045201) ... 0.034060(0.005541)
    XZ              @9: 1.120973(0.052281) ... 0.426980(0.204756)
    VCBLOCKSORT     @9: 1.343682(0.049022) ... 0.041354(0.029944)
    SNAPPY          @9: 1.352733(0.331955) ... 0.006145(0.000629)
    SMAZ            @9: 1.960071(0.087661) ... 0.007363(0.008861)

    Method compression (n = 28202)
    XZ              @9: 1.080121(0.059375) ... 0.605741(0.493482)
    BZ2             @3: 1.087536(0.048270) ... 0.072540(0.206780)
    BZ2             @7: 1.087536(0.048270) ... 0.069770(0.206263)
    BZ2             @4: 1.087536(0.048270) ... 0.071439(0.206454)
    BZ2             @6: 1.087536(0.048270) ... 0.070089(0.206215)
    BZ2             @9: 1.087536(0.048270) ... 0.069295(0.206380)
    BZ2             @2: 1.087536(0.048270) ... 0.074855(0.207004)
    BZ2             @5: 1.087536(0.048270) ... 0.070678(0.206670)
    BZ2             @1: 1.087536(0.048270) ... 0.087981(0.210318)
    BZ2             @8: 1.087536(0.048270) ... 0.069418(0.206200)
    LZMA            @9: 1.094491(0.056935) ... 53.421661(1.259712)
    LZMA            @7: 1.094491(0.056935) ... 53.574627(1.226994)
    LZMA            @8: 1.094491(0.056935) ... 53.486380(1.258273)
    ZLIB            @9: 1.094682(0.045768) ... 0.015043(0.010345)
    ZLIB            @8: 1.094682(0.045768) ... 0.015350(0.010747)
    LZMA            @5: 1.094704(0.056923) ... 27.228655(0.433938)
    LZMA            @6: 1.094704(0.056923) ... 53.881090(1.006792)
    ZLIB            @7: 1.095081(0.046159) ... 0.015739(0.010817)
    ZLIB            @6: 1.095108(0.046272) ... 0.015980(0.011023)
    LZMA            @2: 1.095157(0.057042) ... 0.257422(0.019305)
    LZMA            @1: 1.095157(0.057042) ... 0.195754(0.021020)
    LZMA            @3: 1.095157(0.057041) ... 0.673744(0.019880)
    LZMA            @4: 1.095157(0.057041) ... 2.365907(0.030833)
    ZLIB            @5: 1.097555(0.047478) ... 0.016735(0.011553)
    ZLIB            @4: 1.099069(0.048957) ... 0.017481(0.011628)
    ZLIB            @3: 1.099103(0.048689) ... 0.015914(0.008185)
    ZLIB            @2: 1.099776(0.049330) ... 0.017423(0.008512)
    ZLIB            @1: 1.102691(0.052558) ... 0.033379(0.009507)
    VCBLOCKSORT     @9: 1.284241(0.050310) ... 0.086214(0.143441)
    SNAPPY          @9: 1.353169(0.341400) ... 0.006524(0.001538)
    SMAZ            @9: 1.899097(0.095964) ... 0.019594(0.037356)



The results might lead to the opinion that the compression algorithms SMAZ, SNAPPY and VCBLOCKSORT are quite useless.
The best performing methods are BZ2 and LZMA. Interesstingly, for Methods XZ seems to be better than BZ2.
SNAPPY which was used as the default compression method in the old papers seems to be not very good.
Moreover, it looks like the compression level for BZ2 and ZLIB does not really matter.
One reason might be that BZ2 and ZLIB are block-sorting algorithms, where the level just defines the windows size.
For example in BZ2, the level gives the window size in 100k blocks, hence the results just show that we never
had any inputs larger than 100k length.
For LZMA the compression level makes some difference but for levels larger than 4, the compression is very slow compared to the other methods.
The data would suggest that the best method (in terms of idempotecy) would actually be BZ2 at compression level 2.
SNAPPY is maybe four times faster but has less accuracy.

A different result shows a benchmark with (high entropy) random bytes of length 100k:

    LZMA            @9: 1.000824(0.000005) ... 96.906314(0.709210)
    LZMA            @7: 1.000824(0.000005) ... 96.950522(0.647949)
    LZMA            @5: 1.000824(0.000005) ... 68.139003(0.543345)
    LZMA            @8: 1.000824(0.000005) ... 96.893094(0.637075)
    LZMA            @6: 1.000824(0.000005) ... 96.025901(0.758217)
    LZMA            @2: 1.000831(0.000005) ... 20.485139(0.162692)
    LZMA            @3: 1.000831(0.000005) ... 20.684646(0.431374)
    LZMA            @4: 1.000831(0.000005) ... 27.045070(0.465926)
    VCBLOCKSORT     @9: 1.005893(0.000206) ... 72.661333(0.381322)
    XZ              @9: 1.006252(0.000098) ... 114.364478(0.811344)
    BZ2             @3: 1.243045(0.000274) ... 76.561857(0.487404)
    BZ2             @4: 1.243045(0.000274) ... 76.565262(0.516064)
    BZ2             @6: 1.243045(0.000274) ... 76.578056(0.417544)
    BZ2             @9: 1.243045(0.000274) ... 76.526105(0.404556)
    BZ2             @5: 1.243045(0.000274) ... 76.568458(0.543871)
    BZ2             @8: 1.243045(0.000274) ... 76.566474(0.398533)
    BZ2             @7: 1.243045(0.000274) ... 76.546269(0.402482)
    BZ2             @2: 1.243652(0.000275) ... 76.467374(0.458110)
    LZMA            @1: 1.999293(0.000033) ... 30.468742(0.251365)
    BZ2             @1: 1.999539(0.000183) ... 37.968300(0.380109)
    ZLIB            @1: 1.999890(0.000000) ... 6.402852(0.175904)
    ZLIB            @4: 1.999890(0.000000) ... 6.734575(0.142308)
    ZLIB            @3: 1.999890(0.000000) ... 6.389816(0.147019)
    ZLIB            @8: 1.999890(0.000000) ... 6.733034(0.102385)
    ZLIB            @6: 1.999890(0.000000) ... 6.734264(0.121446)
    ZLIB            @2: 1.999890(0.000000) ... 6.390341(0.158517)
    ZLIB            @9: 1.999890(0.000000) ... 6.733518(0.098179)
    ZLIB            @5: 1.999890(0.000000) ... 6.735792(0.132095)
    ZLIB            @7: 1.999890(0.000000) ... 6.734221(0.112223)
    SNAPPY          @9: 1.999970(0.000001) ... 0.075219(0.003417)
    SMAZ            @9: 1.999989(0.000007) ... 17.743943(0.115701)


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

