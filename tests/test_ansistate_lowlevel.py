"""
Low-level ANSIState / private-helper tests.

These lock in internal representation and parser details rather than
public wrap/fill/shorten behavior. Prefer the property and behavioral
tests in test_ansiwrap.py and test_properties.py for new coverage.

Kept for now for regression safety; candidate for removal once the
content-level suite has proven itself.
"""

import pytest

from ansiwrap.ansistate import ANSIState
from ansiwrap.core import _ansi_optimize


def test_ANSIState_bad_states():
    a = ANSIState()
    with pytest.raises(ValueError):
        a.consume("\x1b[38;7;200m")

    a = ANSIState()
    with pytest.raises(ValueError):
        a.consume("\x1b[48;7;200m")


def test_ANSIState_misc():
    a = ANSIState()
    a.consume("\x1b[33m")
    assert repr(a) == "ANSIState(fg=33, bg=None, style=None)"
    assert str(a) == "(33, —, —)"


def test_optimize():
    s = "\x1b[K\x1b[33msomething\x1b[0m\x1b[K"
    answer = "\x1b[33msomething\x1b[0m"
    assert _ansi_optimize(s) == answer


def test_ANSIState_non_sgr_codes():
    """
    Non-SGR and erase-line sequences are ignored without changing state.
    """
    a = ANSIState()
    a.consume("\x1b[K")
    assert a.fg is None
    assert a.bg is None
    assert a.style is None

    a.consume("\x1b[A")
    assert a.fg is None


def test_ANSIState_reset_and_defaults():
    a = ANSIState(fg=31, bg=42, style=[1, 3])
    a.consume("\x1b[0m")
    assert a.fg is None
    assert a.bg is None
    assert a.style is None
    assert a.code() == ""


def test_ANSIState_standard_colors():
    a = ANSIState()
    a.consume("\x1b[31;43;1m")
    assert a.fg == 31
    assert a.bg == 43
    assert a.style == [1]
    assert a.code() == "\x1b[31;43;1m"

    a.consume("\x1b[39;49m")
    assert a.fg is None
    assert a.bg is None
    assert a.code() == "\x1b[1m"


def test_ANSIState_style_on_off():
    a = ANSIState()
    a.consume("\x1b[1m")
    a.consume("\x1b[1m")  # duplicate bold should not stack
    assert a.style == [1]

    a.consume("\x1b[3m")
    assert a.style == [1, 3]

    a.consume("\x1b[21m")  # turn off bold, leave italic
    assert a.style == [3]

    a.consume("\x1b[23m")  # turn off last style -> None
    assert a.style is None
    assert a.code() == ""


def test_ANSIState_style_off_without_on():
    a = ANSIState()
    a.consume("\x1b[21m")  # bold off with no active styles
    assert a.style is None


def test_ANSIState_truecolor_and_256():
    a = ANSIState()
    a.consume("\x1b[38;5;196m")
    assert a.fg == (38, 5, 196)
    assert a.code() == "\x1b[38;5;196m"

    a.consume("\x1b[38;2;10;20;30m")
    assert a.fg == (38, 2, 10, 20, 30)
    assert a.code() == "\x1b[38;2;10;20;30m"

    a.consume("\x1b[48;5;55m")
    assert a.bg == (48, 5, 55)
    assert a.code() == "\x1b[38;2;10;20;30;48;5;55m"

    a.consume("\x1b[48;2;1;2;3m")
    assert a.bg == (48, 2, 1, 2, 3)
    assert a.code() == "\x1b[38;2;10;20;30;48;2;1;2;3m"

    a.consume("\x1b[48;5;55;1m")  # 256-color bg followed by bold in same sequence
    assert a.bg == (48, 5, 55)
    assert a.style == [1]


def test_ANSIState_code_without_escape_prefix():
    a = ANSIState()
    a.consume("33m")
    assert a.fg == 33
    assert a.code() == "\x1b[33m"


def test_ANSIState_codearr_string_value():
    a = ANSIState(fg="31")
    assert a.code() == "\x1b[31m"


def test_ANSIState_unrecognized_sgr_parameter():
    a = ANSIState()
    a.consume("\x1b[31;99m")  # 99 is not handled; fg still set
    assert a.fg == 31
    assert a.code() == "\x1b[31m"
