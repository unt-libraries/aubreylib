#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='aubreylib',
    version='1.0.0',
    author='University of North Texas Libraries',
    url='https://github.com/unt-libraries/aubreylib',
    license='BSD',
    packages=['aubreylib'],
    install_requires=[
        'lxml>=3.3.3',
        'pyuntl>=1.0.0',
        'pypairtree>=1.0.0',
    ],
)
