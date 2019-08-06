#!/usr/bin/env python

from setuptools import setup

setup(
    name='aubreylib',
    version='1.2.2',
    description='A helper library for the Aubrey access system.',
    author='University of North Texas Libraries',
    author_email='mark.phillips@unt.edu',
    url='https://github.com/unt-libraries/aubreylib',
    license='BSD',
    packages=['aubreylib'],
    install_requires=[
        'lxml>=3.3.3',
        'pypairtree>=1.0.0',
    ],

    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
    ]
)
