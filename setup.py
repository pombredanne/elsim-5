from setuptools import setup, find_packages, Extension

setup(
        name='elsim',
        description='Elsim is a library designed to detect similar content in files, especially in the context of Android',
        packages=find_packagaes(),
        install_requires=[
            "androguard>=3.3.5",
            "numpy",  # only used once, not sure if actual dependency or just some optional stuff
            "sklearn",  # only used once, not sure if actual dependency or just some optional stuff
            ],
        ext_modules=[
            Extension(
                'elsim.elsign.libelsign.libelsign',
                sources=['elsim/elsign/libelsign/elsign.cc'],
                libraries=[]
            )
            ],

        )
