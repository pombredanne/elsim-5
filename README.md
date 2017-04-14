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
