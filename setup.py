# This is the setup file for pip
from setuptools import setup, find_packages
import os, sys
from os import path

setup(
    name = 'hurricane',

    version = '0.0.1',

    description = 'A master-slave computer communication protocol',

    url = 'https://github.com/DarkmatterVale/hurricane',

    author = 'Vale Tolpegin',
    author_email = 'valetolpegin@gmail.com',

    license = 'MIT',

    classifiers = [
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',

        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Information Analysis',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3.5',

        "Operating System :: OS Independent",
    ],

    packages = find_packages(),

    install_requires = [],

    keywords = [],
)
