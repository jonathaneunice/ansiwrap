"""
Behavioral and golden tests for the ansiwrap public API.

Human-authored cases for wrap, fill, shorten, and indent. Low-level
``ANSIState`` checks live in ``test_ansistate_lowlevel``; Hypothesis
properties live in ``test_properties``.
"""

import random
import textwrap

from colors import *  # noqa: F403

from ansiwrap import *  # noqa: F403

LINE_LENGTHS = [20, 27, 40, 41, 42, 43, 55, 70, 78, 79, 80, 100]

other_lengths = random.sample(list(set(range(20, 120)).difference(LINE_LENGTHS)), 2) + random.sample(
    list(set(range(120, 400)).difference(LINE_LENGTHS)), 1
)
LINE_LENGTHS.extend(other_lengths)


def striplines(lines):
    """
    Return ``lines`` with CSI color sequences stripped from each entry.

    Used when comparing ansiwrap layout to plain ``textwrap`` output.
    """
    return [strip_color(line) for line in lines]


def lengths(lines):
    """
    Return the raw ``len`` of each string in ``lines``.

    Callers that need visible width should strip CSI first (see ``striplines``).
    """
    return [len(line) for line in lines]


def same_behavior(text, width, **kwargs):
    """
    Assert ansiwrap matches textwrap layout on CSI-stripped text.

    Checks line count and visible characters per line for ``wrap``, and
    filled length for ``fill``, against ``textwrap`` on the colorless
    string.
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
    """
    Assert wrap/fill layout matches textwrap on mixed ansicolors prose.

    Runs ``same_behavior`` across the shared ``LINE_LENGTHS`` set.
    """
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
    """
    Assert wrap/fill layout matches textwrap when newlines mix with colors.

    Same layout oracle as ``test_one``, with embedded ``\\n`` in the source.
    """
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
    """
    Assert the unified ``indent`` kwarg matches textwrap indent behavior.

    Covers int and str forms, and mixed ``(initial, subsequent)`` tuples,
    against ``initial_indent`` / ``subsequent_indent`` on colorless text.
    """
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
        """
        Compare ansiwrap and textwrap line lengths at one width and indent pair.

        ``kw1`` is passed to ``wrap``; ``kw2`` is the equivalent textwrap kwargs.
        """
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

    Includes EL, terse reset, truecolor, and style on/off sequences while
    still matching ``textwrap.fill`` on the stripped string.
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


def test_unterminated():
    """
    Assert open SGR is closed per line and reopened on the next.

    Golden output for a long yellow span that wraps without a prior reset.
    """
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
    """
    Assert exact wrap output for a fixed multi-color gibberish paragraph.

    Human-verified golden lines at width 30, including mid-line color breaks.
    """
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
    """
    Assert shorten truncates plain and colored text with placeholders.

    Covers default ``[...]``, colored placeholders, and a Latin-1 character.
    """
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
    """
    Assert the README-style example string, fill, and shorten outputs.

    Pins the documented ansicolors composition and its wrap/shorten results.
    """
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
    """
    Assert shorten returns empty for empty or whitespace-only input.

    Matches textwrap-style collapse of blank content before truncation.
    """
    assert shorten("", 79) == ""
    assert shorten(" ", 50) == ""
    assert shorten("   ", 55) == ""
