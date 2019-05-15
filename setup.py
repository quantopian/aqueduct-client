#!/usr/bin/env python
from setuptools import setup, find_packages
import sys

long_description = ''

if 'upload' in sys.argv:
    with open('README.rst') as f:
        long_description = f.read()


def install_requires():
    return [
        'pandas',
        'requests',
    ]


setup(
    name='aqueduct-client',
    version='0.1',
    description="Python wrapper for Quantopian's Aqueduct API",
    author="Quantopian",
    author_email="support@quantopian.com",
    packages=find_packages(),
    long_description=long_description,
    license='Apache 2.0',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Office/Business :: Financial',
    ],
    url='https://github.com/quantopian/aqueduct-client',
    install_requires=install_requires(),
)
