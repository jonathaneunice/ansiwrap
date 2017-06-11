#!/usr/bin/env python

from setuptools import setup
from codecs import open


def lines(text):
    """
    Returns each non-blank line in text enclosed in a list.
    See http://pypi.python.org/pypi/textdata for more sophisticated version.
    """
    return [l.strip() for l in text.strip().splitlines() if l.strip()]


setup(
    name='ansiwrap',
    version='0.8.2',
    author='Jonathan Eunice',
    author_email='jonathan.eunice@gmail.com',
    description="textwrap, but savvy to ANSI colors and styles",
    long_description=open('README.rst', encoding='utf-8').read(),
    url='https://github.com/jonathaneunice/ansiwrap',
    license='Apache License 2.0',
    packages=['ansiwrap'],
    setup_requires=[],
    install_requires=['textwrap3'],
    tests_require=['tox', 'pytest', 'ansicolors>=1.1.8', 'coverage', 'pytest-cov'],
    test_suite="test",
    zip_safe=False,
    keywords='text textwrap ANSI colors',
    classifiers=lines("""
        Development Status :: 4 - Beta
        Environment :: Console
        Operating System :: OS Independent
        License :: OSI Approved :: Apache Software License
        Intended Audience :: Developers
        Programming Language :: Python
        Programming Language :: Python :: 2
        Programming Language :: Python :: 2.6
        Programming Language :: Python :: 2.7
        Programming Language :: Python :: 3
        Programming Language :: Python :: 3.3
        Programming Language :: Python :: 3.4
        Programming Language :: Python :: 3.5
        Programming Language :: Python :: 3.6
        Programming Language :: Python :: Implementation :: CPython
        Programming Language :: Python :: Implementation :: PyPy
        Topic :: Software Development :: Libraries :: Python Modules
        Topic :: Text Processing
        Topic :: Text Processing :: Filters
    """)
)
