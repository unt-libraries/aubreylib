#!/usr/bin/env python

from setuptools import setup

setup(
    name='aubreylib',
    version='2.0.0',
    description='A helper library for the Aubrey access system.',
    author='University of North Texas Libraries',
    author_email='mark.phillips@unt.edu',
    url='https://github.com/unt-libraries/aubreylib',
    license='BSD',
    packages=['aubreylib'],
    install_requires=[
        'lxml>=3.3.3',
        'pypairtree @ git+https://github.com/unt-libraries/pypairtree.git@master#egg=pypairtree',
        'pyuntl @ git+https://github.com/unt-libraries/pyuntl.git@master#egg=pyuntl',
    ],

    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ]
)
