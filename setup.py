from setuptools import setup, find_packages, Extension

libraries = ['lzma', 'muparser', 'snappy', 'bz2', 'z']

setup(
        name='elsim',
        description='Elsim is a library designed to detect similar content in files, especially in the context of Android',
        packages=find_packages(),
        install_requires=[
            "androguard>=3.3.5",
            "numpy",  # only used once, not sure if actual dependency or just some optional stuff
            "sklearn",  # only used once, not sure if actual dependency or just some optional stuff
            ],
        ext_modules=[
            Extension(
                'elsim.similarity.libsimilarity.libsimilarity',
                sources=['elsim/similarity/libsimilarity/similarity.c'],
                libraries=libraries,
            ),
            Extension(
                'elsim.elsign.libelsign.libelsign',
                sources=['elsim/elsign/libelsign/elsign.cc'],
                libraries=libraries,
                include_dirs=['elsim/similarity/libsimilarity'],
                extra_compile_args=['-D_GLIBCXX_PERMIT_BACKWARD_HASH']
            )
            ],

        )
