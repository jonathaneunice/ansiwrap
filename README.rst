
.. image:: https://img.shields.io/pypi/v/ansiwrap.svg
   :target: https://pypi.org/project/ansiwrap

.. image:: https://github.com/jonathaneunice/ansiwrap/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/jonathaneunice/ansiwrap/actions/workflows/ci.yml

.. image:: https://img.shields.io/pypi/pyversions/ansiwrap.svg
   :target: https://pypi.org/project/ansiwrap

.. figure:: https://raw.githubusercontent.com/jonathaneunice/ansiwrap/main/docs/images/ansiwrap-concept.png
   :alt: ansiwrap: textwrap that understands ANSI color codes

   ``textwrap`` is fooled by ANSI escape codes; ``ansiwrap`` is not.

``ansiwrap`` wraps text, like the standard ``textwrap`` module.
But it also correctly wraps text that contains ANSI control
sequences that colorize or style text.

Where ``textwrap`` is fooled by the raw string length of those control codes,
``ansiwrap`` is not; it understands that however much those codes affect color
and display style, they have no logical length.

The API mirrors the ``wrap``, ``fill``, and ``shorten``
functions of ``textwrap``. For example::

    from colors import *     # ansicolors on PyPI
    from ansiwrap import *

    s = ' '.join([red('this string'),
                  blue('is going on a bit long'),
                  green('and may need to be'),
                  color('shortened a bit', fg='purple')])

    print('-- original string --')
    print(s)
    print('-- now filled --')
    print(fill(s, 20))
    print('-- now shortened / truncated --')
    print(shorten(s, 20, placeholder='...'))

It also exports several other functions:

* ``ansilen`` (giving the effective length of a string, ignoring ANSI control codes)
* ``ansi_terminate_lines`` (propagates control codes though a list of strings/lines
  and terminates each line.)
* ``strip_color`` (removes ANSI control codes from a string)

See also the enclosed ``demo.py``.
