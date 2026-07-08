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
    """
    Assert invalid 38/48 color subtypes raise ``ValueError``.

    Covers ``38;7`` and ``48;7``, which are not 256-color or truecolor.
    """
    a = ANSIState()
    with pytest.raises(ValueError):
        a.consume("\x1b[38;7;200m")

    a = ANSIState()
    with pytest.raises(ValueError):
        a.consume("\x1b[48;7;200m")


def test_ANSIState_misc():
    """
    Assert ``repr`` and ``str`` for a simple foreground-only state.

    Locks the debug formatting used when inspecting ``ANSIState``.
    """
    a = ANSIState()
    a.consume("\x1b[33m")
    assert repr(a) == "ANSIState(fg=33, bg=None, style=None)"
    assert str(a) == "(33, —, —)"


def test_optimize():
    """
    Assert ``_ansi_optimize`` strips erase-line codes from a sample string.

    Private helper; kept here with other low-level checks.
    """
    s = "\x1b[K\x1b[33msomething\x1b[0m\x1b[K"
    answer = "\x1b[33msomething\x1b[0m"
    assert _ansi_optimize(s) == answer


def test_ANSIState_non_sgr_codes():
    """
    Ignore non-SGR and erase-line sequences without changing state.

    ``\\x1b[K`` and cursor codes such as ``\\x1b[A`` must leave fg/bg/style
    untouched.
    """
    a = ANSIState()
    a.consume("\x1b[K")
    assert a.fg is None
    assert a.bg is None
    assert a.style is None

    a.consume("\x1b[A")
    assert a.fg is None


def test_ANSIState_reset_and_defaults():
    """
    Assert ``0`` clears fg, bg, and style and yields an empty ``code()``.

    Starts from a fully populated state before consuming reset.
    """
    a = ANSIState(fg=31, bg=42, style=[1, 3])
    a.consume("\x1b[0m")
    assert a.fg is None
    assert a.bg is None
    assert a.style is None
    assert a.code() == ""


def test_ANSIState_standard_colors():
    """
    Assert combined SGR parsing and default fg/bg restoration.

    Checks ``code()`` after ``31;43;1`` and after ``39;49`` leaves bold only.
    """
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


def test_ANSIState_bright_colors():
    """
    Assert aixterm bright FG/BG (90–97, 100–107) parse and round-trip.

    Bright codes must set fg/bg so wrap reopen emits them; ``39``/``49``
    clear them like classic colors. Combined bright + style must survive
    ``code()``.
    """
    a = ANSIState()
    a.consume("\x1b[91m")
    assert a.fg == 91
    assert a.code() == "\x1b[91m"

    a.consume("\x1b[103m")
    assert a.fg == 91
    assert a.bg == 103
    assert a.code() == "\x1b[91;103m"

    a.consume("\x1b[1m")
    assert a.style == [1]
    assert a.code() == "\x1b[91;103;1m"

    a.consume("\x1b[39;49m")
    assert a.fg is None
    assert a.bg is None
    assert a.code() == "\x1b[1m"

    a = ANSIState()
    a.consume("\x1b[97;107;1m")
    assert a.fg == 97
    assert a.bg == 107
    assert a.style == [1]
    assert a.code() == "\x1b[97;107;1m"

    # Bright replaces classic (and vice versa) as the active fg/bg.
    a.consume("\x1b[31m")
    assert a.fg == 31
    a.consume("\x1b[94m")
    assert a.fg == 94
    assert a.code() == "\x1b[94;107;1m"


def test_ANSIState_style_on_off():
    """
    Assert style attrs accumulate, dedupe, and turn off via 2x codes.

    Bold must not stack; ``21``/``23`` remove bold/italic until style is empty.
    """
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
    """
    Assert turning off a style that was never set leaves style as ``None``.

    ``21`` (bold off) on a fresh state must be a no-op.
    """
    a = ANSIState()
    a.consume("\x1b[21m")  # bold off with no active styles
    assert a.style is None


def test_ANSIState_truecolor_and_256():
    """
    Assert 256-color and truecolor fg/bg parsing and ``code()`` round-trips.

    Also covers a 256-color bg followed by bold in the same CSI sequence.
    """
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
    """
    Assert ``consume`` accepts bodies without the ``ESC[`` prefix.

    ``33m`` should set fg and ``code()`` should emit a full CSI sequence.
    """
    a = ANSIState()
    a.consume("33m")
    assert a.fg == 33
    assert a.code() == "\x1b[33m"


def test_ANSIState_codearr_string_value():
    """
    Assert ``code()`` accepts a string fg value set at construction.

    ``ANSIState(fg="31")`` must still emit ``\\x1b[31m``.
    """
    a = ANSIState(fg="31")
    assert a.code() == "\x1b[31m"


def test_ANSIState_unrecognized_sgr_parameter():
    """
    Assert unknown SGR params are ignored without dropping known ones.

    ``31;99`` should keep fg 31 and omit 99 from ``code()``.
    """
    a = ANSIState()
    a.consume("\x1b[31;99m")  # 99 is not handled; fg still set
    assert a.fg == 31
    assert a.code() == "\x1b[31m"
