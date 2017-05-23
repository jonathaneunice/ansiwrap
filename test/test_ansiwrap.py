# -*- coding: utf-8 -*-

import textwrap
from colors import *  # must come before ansiwrap import
                      # so ansiwrap's better strip_color prevails

from ansiwrap import *
from ansiwrap.core import _ansi_optimize
from ansiwrap.ansistate import ANSIState

import pytest
import random
import sys

_PY2 = sys.version_info[0] == 2

# explict test-at line lengths
LINE_LENGTHS = [20, 27, 40, 41, 42, 43, 55, 70, 78, 79, 80, 100]

# as an alternative to testing all lengths at all times, which is slow,
# choose a few other lengths at random
other_lengths = (random.sample(set(range(20, 120)).difference(LINE_LENGTHS), 2) +
                 random.sample(set(range(120, 400)).difference(LINE_LENGTHS), 1))
LINE_LENGTHS.extend(other_lengths)



def striplines(lines):
    return [strip_color(line) for line in lines]

def lengths(lines):
    return [len(line) for line in lines]

def same_behavior(text, width, **kwargs):
    """
    Comparison fixture. Did ansiwrap wrap the text to the same number
    of lines, with the same number of visible characters per line, as textwrap
    did to the text without ANSI codes?
    """
    no_ansi = strip_color(text)
    clean_wrap = textwrap.wrap(no_ansi, width, **kwargs)
    clean_fill = textwrap.fill(no_ansi, width, **kwargs)
    ansi_wrap = wrap(text, width, **kwargs)
    ansi_fill = fill(text, width, **kwargs)

    clean_wrap_lens = lengths(clean_wrap)
    ansi_wrap_lens = lengths(striplines(ansi_wrap))

    assert len(clean_wrap) == len(ansi_wrap)
    assert len(clean_fill) == len(strip_color(ansi_fill))
    assert clean_wrap_lens == ansi_wrap_lens


def test_one():
    # old demo text
    text = (red('This') + ' is ' + color('some', fg=11, bg=55, style='bold') +
            blue(' very nice') + ' ' + yellow('colored') +
            ' text ' + green('that is hard to') + yellow(' nicely ')
            + green('wrap because') +
            red(' of the ') + blue('ANSI', bg='yellow') + yellow(' codes.') +
            red(' But') + blue(' ansiwrap ') + green('does fine.'))
    for width in LINE_LENGTHS:
        same_behavior(text, width)


def test_two():
    # new demo text
    text = ('textwrap\ndoes\nplain\ntext\nwell.\n' + red('But') + ' text ' +
           color('colored', fg=11, bg=55, style='bold') +
           yellow(' with ') + red('embedded ') + blue('ANSI', bg='yellow') +
           green(' codes') + yellow('?')
           + green(' Not') +
           red(' so ') + blue('good ') + magenta('there') + cyan('.')
           + color(' ansiwrap ', style='italic') +
           yellow('has') + red(' no') + green(' such ') + blue('limits.'))
    for width in LINE_LENGTHS:
        same_behavior(text, width)


def test_unified_indent():
    text = ('textwrap\ndoes\nplain\ntext\nwell.\n' + red('But') + ' text ' +
           color('colored', fg=11, bg=55, style='bold') +
           yellow(' with ') + red('embedded ') + blue('ANSI', bg='yellow') +
           green(' codes') + yellow('?')
           + green(' Not') +
           red(' so ') + blue('good ') + magenta('there') + cyan('.')
           + color(' ansiwrap ', style='italic') +
           yellow('has') + red(' no') + green(' such ') + blue('limits.'))
    no_ansi = strip_color(text)

    def test_at_width(w, kw1, kw2):
        ansi_lines = wrap(text, w, **kw1)
        clean_lines = textwrap.wrap(no_ansi, w, **kw2)
        ansi_lens = lengths(striplines(ansi_lines))
        clean_lens = lengths(clean_lines)
        assert ansi_lens == clean_lens

    WIDTHS = [0, 1, 2, 4, 5, 8, 10]
    max_indent = 9
    for width in LINE_LENGTHS:
        for indent_width in WIDTHS:
            indent_str = ' ' * indent_width
            test_at_width(width, dict(indent=indent_width),
                                 dict(initial_indent=indent_str,
                                      subsequent_indent=indent_str))

    for width in LINE_LENGTHS:
        for indent_width in WIDTHS:
            for indent_width2 in WIDTHS:

                indent_str = ' ' * indent_width
                indent_str2 = ' ' * indent_width2

                # integer tuple
                test_at_width(width, dict(indent=(indent_width, indent_width2)),
                                     dict(initial_indent=indent_str,
                                          subsequent_indent=indent_str2))
                # mixed tuple
                test_at_width(width, dict(indent=(indent_width, indent_str2)),
                                     dict(initial_indent=indent_str,
                                          subsequent_indent=indent_str2))
                test_at_width(width, dict(indent=(indent_str, indent_width2)),
                                     dict(initial_indent=indent_str,
                                          subsequent_indent=indent_str2))

                # string tuple
                test_at_width(width, dict(indent=(indent_str, indent_str2)),
                                     dict(initial_indent=indent_str,
                                          subsequent_indent=indent_str2))

def test_odd_states():
    """
    Attempt to put in codes that are not often seen with ansicolors module,
    but that are legit ANSI codes and used by other text processors. These inluce
    erase to end of line (EL) common in grep output, sepecifc style turn-offs
    that aren't "turn off everything," and truncated "turn off evertying."
    """

    EL = '\x1b[K'

    text = ('textwrap\ndoes\nplain\ntext\nwell.\n' + red('But') + ' text ' +
           color('colored', fg=11, bg=55, style='bold') +
           yellow(' with ') + red('embedded ', style='underline') + blue('ANSI', bg='yellow') +
           green(' codes') + '\x1b[2;33;43m?\x1b[39;49m\x1b[m' + EL +
           green(' Not') + '\x1b[39m' + '\x1b[49m' + '\x1b[1m\x1b[21m' +
           red(' so ') + '\x1b[38;2;12;23;39;48;2;10;10;10mmgood\x1b[m ' +
           magenta('there') + cyan('.') + EL +
           color(' ansiwrap ', style='italic') +
           yellow('has') + red(' no') + green(' such ') + blue('limits.'))

    no_ansi = strip_color(text)

    for width in LINE_LENGTHS:
        assert strip_color(fill(text, width)) == textwrap.fill(no_ansi, width)


def test_ANSIState_bad_states():
    a = ANSIState()
    with pytest.raises(ValueError):
        a.consume('\x1b[38;7;200m')

    a = ANSIState()
    with pytest.raises(ValueError):
        a.consume('\x1b[48;7;200m')



def test_ANSIState_misc():

    a = ANSIState()
    a.consume('\x1b[33m')
    assert repr(a) == 'ANSIState(fg=33, bg=None, style=None)'

    stringify = unicode if _PY2 else str
    str_a = stringify(a)
    assert str_a == u'(33, —, —)'


def test_optimize():
    s = '\x1b[K\x1b[33msomething\x1b[0m\x1b[K'
    answer = '\x1b[33msomething\x1b[0m'
    assert _ansi_optimize(s) == answer


def test_unterminated():
    s = 'this is \x1b[33mgood and things are okay but very long and do not  really fit on one line so maybe wrapping?'
    w = wrap(s, 50)
    assert w == ['this is \x1b[33mgood and things are okay but very long and\x1b[0m',
                 '\x1b[33mdo not  really fit on one line so maybe wrapping?\x1b[0m']

def test_known_text():
    """Trst random text against a known good wrapping."""
    r = ('gk zjpwxwqzq mnbafwsr agimmnmnv ylgy ebcdzrkfi eixtigdt skoxq zgjpqvrhf'
        ' i cuwdkjtl bhzljgwsd ljyq zjsem qgdn kwsc \x1b[31ml khcgnkl emxk wl svm '
        'ynk seumlnqhrh fxewvci\x1b[0m jxfbkiwwmz wdjwpw ndggihphir wcjftt t shzd '
        'cirjue kaxj fhw qezkffo knkag \x1b[33myfw cfpe uefaeywiq\x1b[0m rixxxykzd '
        'wu zcvfjbfy pcvhgqksxw uifumuxipr z \x1b[35mfm r vnvlc nnjbhwdjfv '
        'vkpxddyrsf obrlfup gghbvg nxfcqasnzf hj\x1b[0m')
    w = wrap(r, 30)
    assert w == ['gk zjpwxwqzq mnbafwsr',
                 'agimmnmnv ylgy ebcdzrkfi',
                 'eixtigdt skoxq zgjpqvrhf i',
                 'cuwdkjtl bhzljgwsd ljyq zjsem',
                 'qgdn kwsc \x1b[31ml khcgnkl emxk wl\x1b[0m',
                 '\x1b[31msvm ynk seumlnqhrh fxewvci\x1b[0m',
                 'jxfbkiwwmz wdjwpw ndggihphir',
                 'wcjftt t shzd cirjue kaxj fhw',
                 'qezkffo knkag \x1b[33myfw cfpe\x1b[0m',
                 '\x1b[33muefaeywiq\x1b[0m rixxxykzd wu',
                 'zcvfjbfy pcvhgqksxw uifumuxipr',
                 'z \x1b[35mfm r vnvlc nnjbhwdjfv\x1b[0m',
                 '\x1b[35mvkpxddyrsf obrlfup gghbvg\x1b[0m',
                 '\x1b[35mnxfcqasnzf hj\x1b[0m']
