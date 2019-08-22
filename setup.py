from setuptools import setup, find_packages, Extension


setup(
    name='elsim',
    description='Elsim is a library designed to detect similar content in files, especially in the context of Android',
    packages=find_packages(),
    install_requires=[
        "androguard>=3.3.5",
        "python-hashes",
        "numpy",  # only used once, not sure if actual dependency or just some optional stuff
        "sklearn",  # only used once, not sure if actual dependency or just some optional stuff
    ],
    ext_modules=[
        Extension(
            'elsim.similarity.libsimilarity',
            sources=['elsim/similarity/similarity.c',
                     'elsim/similarity/bz2/bz2.c',
                     'elsim/similarity/lzma/Alloc.c',
                     'elsim/similarity/lzma/LzFind.c',
                     'elsim/similarity/lzma/LzmaDec.c',
                     'elsim/similarity/lzma/LzmaEnc.c',
                     'elsim/similarity/lzma/LzmaLib.c',
                     'elsim/similarity/lzma/lzma.c',
                     'elsim/similarity/smaz/smaz.c',
                     'elsim/similarity/snappy/snappy.cc',
                     'elsim/similarity/vcblocksort/vcblocksort.c',
                     'elsim/similarity/xz/xz.c',
                     'elsim/similarity/z/z.c',
                     ],
            libraries=['lzma', 'snappy', 'bz2', 'z'],
            extra_compile_args=[
                '-D_7ZIP_ST',  # required for LZMA
            ],
        ),
        Extension(
            'elsim.elsign.libelsign',
            sources=['elsim/elsign/elsign.cc',
                     'elsim/elsign/ac_heap.c',
                     'elsim/elsign/ac_list.c',
                     'elsim/elsign/aho_corasick.c',
                     'elsim/elsign/cluster.c',
                     'elsim/elsign/formula.cc',

                     # FIXME: this is a crude hack to get it to work!!!
                     # idealy, one would link against the other library, but this seems to be very hard to do...
                     'elsim/similarity/similarity.c',
                     'elsim/similarity/bz2/bz2.c',
                     'elsim/similarity/lzma/Alloc.c',
                     'elsim/similarity/lzma/LzFind.c',
                     'elsim/similarity/lzma/LzmaDec.c',
                     'elsim/similarity/lzma/LzmaEnc.c',
                     'elsim/similarity/lzma/LzmaLib.c',
                     'elsim/similarity/lzma/lzma.c',
                     'elsim/similarity/smaz/smaz.c',
                     'elsim/similarity/snappy/snappy.cc',
                     'elsim/similarity/vcblocksort/vcblocksort.c',
                     'elsim/similarity/xz/xz.c',
                     'elsim/similarity/z/z.c',
                    ],
            libraries=['muparser', 'lzma', 'snappy', 'bz2', 'z'],
            include_dirs=['elsim/similarity'],
            extra_compile_args=[
                '-D_GLIBCXX_PERMIT_BACKWARD_HASH',  # required for sparsehash
                '-D_7ZIP_ST',  # required for LZMA
                ],
        )
    ],

)
