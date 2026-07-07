"""
Tests for the ansiwrap module.
"""

import random
import textwrap

import pytest
from colors import *  # noqa: F403

from ansiwrap import *  # noqa: F403
from ansiwrap.ansistate import ANSIState
from ansiwrap.core import _ansi_optimize

LINE_LENGTHS = [20, 27, 40, 41, 42, 43, 55, 70, 78, 79, 80, 100]

other_lengths = random.sample(list(set(range(20, 120)).difference(LINE_LENGTHS)), 2) + random.sample(
    list(set(range(120, 400)).difference(LINE_LENGTHS)), 1
)
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
    text = (
        red("This")
        + " is "
        + color("some", fg=11, bg=55, style="bold")
        + blue(" very nice")
        + " "
        + yellow("colored")
        + " text "
        + green("that is hard to")
        + yellow(" nicely ")
        + green("wrap because")
        + red(" of the ")
        + blue("ANSI", bg="yellow")
        + yellow(" codes.")
        + red(" But")
        + blue(" ansiwrap ")
        + green("does fine.")
    )
    for width in LINE_LENGTHS:
        same_behavior(text, width)


def test_two():
    text = (
        "textwrap\ndoes\nplain\ntext\nwell.\n"
        + red("But")
        + " text "
        + color("colored", fg=11, bg=55, style="bold")
        + yellow(" with ")
        + red("embedded ")
        + blue("ANSI", bg="yellow")
        + green(" codes")
        + yellow("?")
        + green(" Not")
        + red(" so ")
        + blue("good ")
        + magenta("there")
        + cyan(".")
        + color(" ansiwrap ", style="italic")
        + yellow("has")
        + red(" no")
        + green(" such ")
        + blue("limits.")
    )
    for width in LINE_LENGTHS:
        same_behavior(text, width)


def test_unified_indent():
    text = (
        "textwrap\ndoes\nplain\ntext\nwell.\n"
        + red("But")
        + " text "
        + color("colored", fg=11, bg=55, style="bold")
        + yellow(" with ")
        + red("embedded ")
        + blue("ANSI", bg="yellow")
        + green(" codes")
        + yellow("?")
        + green(" Not")
        + red(" so ")
        + blue("good ")
        + magenta("there")
        + cyan(".")
        + color(" ansiwrap ", style="italic")
        + yellow("has")
        + red(" no")
        + green(" such ")
        + blue("limits.")
    )
    no_ansi = strip_color(text)

    def test_at_width(w, kw1, kw2):
        ansi_lines = wrap(text, w, **kw1)
        clean_lines = textwrap.wrap(no_ansi, w, **kw2)
        ansi_lens = lengths(striplines(ansi_lines))
        clean_lens = lengths(clean_lines)
        assert ansi_lens == clean_lens

    widths = [0, 1, 2, 4, 5, 8, 10]
    for width in LINE_LENGTHS:
        for indent_width in widths:
            indent_str = " " * indent_width
            test_at_width(
                width,
                dict(indent=indent_width),
                dict(initial_indent=indent_str, subsequent_indent=indent_str),
            )

    for width in LINE_LENGTHS:
        for indent_width in widths:
            for indent_width2 in widths:
                indent_str = " " * indent_width
                indent_str2 = " " * indent_width2

                test_at_width(
                    width,
                    dict(indent=(indent_width, indent_width2)),
                    dict(initial_indent=indent_str, subsequent_indent=indent_str2),
                )
                test_at_width(
                    width,
                    dict(indent=(indent_width, indent_str2)),
                    dict(initial_indent=indent_str, subsequent_indent=indent_str2),
                )
                test_at_width(
                    width,
                    dict(indent=(indent_str, indent_width2)),
                    dict(initial_indent=indent_str, subsequent_indent=indent_str2),
                )
                test_at_width(
                    width,
                    dict(indent=(indent_str, indent_str2)),
                    dict(initial_indent=indent_str, subsequent_indent=indent_str2),
                )


def test_odd_states():
    """
    Exercise ANSI codes not commonly emitted by ansicolors.
    """
    el = "\x1b[K"

    text = (
        "textwrap\ndoes\nplain\ntext\nwell.\n"
        + red("But")
        + " text "
        + color("colored", fg=11, bg=55, style="bold")
        + yellow(" with ")
        + red("embedded ", style="underline")
        + blue("ANSI", bg="yellow")
        + green(" codes")
        + "\x1b[2;33;43m?\x1b[39;49m\x1b[m"
        + el
        + green(" Not")
        + "\x1b[39m"
        + "\x1b[49m"
        + "\x1b[1m\x1b[21m"
        + red(" so ")
        + "\x1b[38;2;12;23;39;48;2;10;10;10mmgood\x1b[m "
        + magenta("there")
        + cyan(".")
        + el
        + color(" ansiwrap ", style="italic")
        + yellow("has")
        + red(" no")
        + green(" such ")
        + blue("limits.")
    )

    no_ansi = strip_color(text)

    for width in LINE_LENGTHS:
        assert strip_color(fill(text, width)) == textwrap.fill(no_ansi, width)


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


def test_unterminated():
    s = (
        "this is \x1b[33mgood and things are okay but very long and do not  "
        "really fit on one line so maybe wrapping?"
    )
    w = wrap(s, 50)
    assert w == [
        "this is \x1b[33mgood and things are okay but very long and\x1b[0m",
        "\x1b[33mdo not  really fit on one line so maybe wrapping?\x1b[0m",
    ]


def test_known_text():
    r = (
        "gk zjpwxwqzq mnbafwsr agimmnmnv ylgy ebcdzrkfi eixtigdt skoxq zgjpqvrhf"
        " i cuwdkjtl bhzljgwsd ljyq zjsem qgdn kwsc \x1b[31ml khcgnkl emxk wl svm "
        "ynk seumlnqhrh fxewvci\x1b[0m jxfbkiwwmz wdjwpw ndggihphir wcjftt t shzd "
        "cirjue kaxj fhw qezkffo knkag \x1b[33myfw cfpe uefaeywiq\x1b[0m rixxxykzd "
        "wu zcvfjbfy pcvhgqksxw uifumuxipr z \x1b[35mfm r vnvlc nnjbhwdjfv "
        "vkpxddyrsf obrlfup gghbvg nxfcqasnzf hj\x1b[0m"
    )
    w = wrap(r, 30)
    assert w == [
        "gk zjpwxwqzq mnbafwsr",
        "agimmnmnv ylgy ebcdzrkfi",
        "eixtigdt skoxq zgjpqvrhf i",
        "cuwdkjtl bhzljgwsd ljyq zjsem",
        "qgdn kwsc \x1b[31ml khcgnkl emxk wl\x1b[0m",
        "\x1b[31msvm ynk seumlnqhrh fxewvci\x1b[0m",
        "jxfbkiwwmz wdjwpw ndggihphir",
        "wcjftt t shzd cirjue kaxj fhw",
        "qezkffo knkag \x1b[33myfw cfpe\x1b[0m",
        "\x1b[33muefaeywiq\x1b[0m rixxxykzd wu",
        "zcvfjbfy pcvhgqksxw uifumuxipr",
        "z \x1b[35mfm r vnvlc nnjbhwdjfv\x1b[0m",
        "\x1b[35mvkpxddyrsf obrlfup gghbvg\x1b[0m",
        "\x1b[35mnxfcqasnzf hj\x1b[0m",
    ]


def test_shorten_basic():
    result = shorten("this is some really long text, no?", 15)
    assert result == "this is [...]"

    result = shorten(red("this is some really long text, no?"), 15)
    assert result == "\x1b[31mthis is [...]\x1b[0m"

    result = shorten(
        red("this is some really long text, no?"),
        15,
        placeholder=green("..."),
    )
    assert result == "\x1b[31mthis is some\x1b[32m...\x1b[0m"

    result = shorten(
        red("this is some really long text, no?"),
        15,
        placeholder=green("\u2026"),
    )
    assert result == "\x1b[31mthis is some\x1b[32m\u2026\x1b[0m"

    result = shorten(
        red("this is \u00fcber long text, no?"),
        15,
        placeholder=green("\u2026"),
    )
    assert result == "\x1b[31mthis is \u00fcber\x1b[32m\u2026\x1b[0m"


def test_doc_example():
    s = " ".join(
        [
            red("this string"),
            blue("is going on a bit long"),
            green("and may need to be"),
            color("shortened a bit", fg="purple"),
        ]
    )

    assert (
        s == "\x1b[31mthis string\x1b[0m \x1b[34mis going on a bit "
        "long\x1b[0m \x1b[32mand may need to be\x1b[0m "
        "\x1b[38;2;128;0;128mshortened a bit\x1b[0m"
    )

    assert (
        fill(s, 20) == "\x1b[31mthis string\x1b[0m \x1b[34mis "
        "going\x1b[0m\n\x1b[34mon a bit long\x1b[0m "
        "\x1b[32mand\x1b[0m\n\x1b[32mmay need to "
        "be\x1b[0m\n\x1b[38;2;128;0;128mshortened a bit\x1b[0m"
    )

    assert shorten(s, 20, placeholder="...") == "\x1b[31mthis string\x1b[0m \x1b[34mis...\x1b[0m"


def test_shorten_trivial():
    assert shorten("", 79) == ""
    assert shorten(" ", 50) == ""
    assert shorten("   ", 55) == ""


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
