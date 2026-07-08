"""
Content-level property tests for ansiwrap.

Layout is checked against textwrap on CSI-stripped text. Style continuity
is checked with the independent render oracle in render_oracle.py
(rendered equality, not exact CSI byte strings).

Existing behavioral/golden tests in test_ansiwrap.py are left alone;
these add breadth via Hypothesis-generated inputs.

Generator note
--------------
SGR is applied around whole words (or left open across words), not injected
between letters. Mid-word CSI combined with ``break_long_words`` is a known
limitation of the current textwrap-len monkey-patch approach; see
``test_known_limitation_midword_csi_break_long_words``.
"""

from __future__ import annotations

import textwrap

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from ansiwrap import ansilen, fill, shorten, strip_color, wrap
from tests.render_oracle import content_chars, final_style, strip_csi, styled_chars

# --- generators -------------------------------------------------------------
#
# Stick to display-width-1 code points (see render_oracle module docstring).

_WORD_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
_LATIN1_EXTRA = "àáâãäåæçèéêëìíîïñòóôõöùúûüýÿ"

plain_char = st.sampled_from(_WORD_CHARS + _LATIN1_EXTRA)

# Openers establish style; closers/resets clear or partially clear it.
sgr_open = st.sampled_from(
    [
        "\x1b[1m",
        "\x1b[3m",
        "\x1b[4m",
        "\x1b[31m",
        "\x1b[32m",
        "\x1b[33m",
        "\x1b[34m",
        "\x1b[35m",
        "\x1b[36m",
        "\x1b[37m",
        "\x1b[41m",
        "\x1b[42m",
        "\x1b[43m",
        # Bright / aixterm FG (90–97) and BG (100–107).
        "\x1b[91m",
        "\x1b[92m",
        "\x1b[93m",
        "\x1b[94m",
        "\x1b[95m",
        "\x1b[96m",
        "\x1b[97m",
        "\x1b[101m",
        "\x1b[104m",
        "\x1b[1;91m",
        "\x1b[91;1m",
        "\x1b[1;31m",
        "\x1b[31;1m",
        "\x1b[3;4m",
        "\x1b[38;5;196m",
        "\x1b[38;5;33m",
        "\x1b[48;5;55m",
        "\x1b[38;2;12;23;39m",
        "\x1b[48;2;10;10;10m",
        "\x1b[38;2;255;0;128;1m",
    ]
)

sgr_close = st.sampled_from(
    [
        "\x1b[0m",
        "\x1b[m",
        "\x1b[21m",
        "\x1b[23m",
        "\x1b[24m",
        "\x1b[39m",
        "\x1b[49m",
        "\x1b[39;49m",
    ]
)

noise = st.sampled_from(["", "", "\x1b[K"])  # EL is zero-width; prefer often absent


@st.composite
def plain_word(draw, min_len=1, max_len=14):
    """
    Draw a single width-1 word with no embedded CSI.

    Length is between ``min_len`` and ``max_len`` inclusive.
    """
    n = draw(st.integers(min_value=min_len, max_value=max_len))
    return "".join(draw(plain_char) for _ in range(n))


@st.composite
def ansi_text(draw, max_words=35):
    """
    Colored prose with CSI only at word boundaries.

    Styles may span multiple words (unterminated until a later reset), which
    exercises reopen/reset across wrap lines without hitting the mid-word
    break_long_words limitation.
    """
    n_words = draw(st.integers(min_value=1, max_value=max_words))
    parts: list[str] = []
    open_span = False
    for i in range(n_words):
        if i:
            sep = draw(st.sampled_from([" ", " ", " ", "  ", "\n"]))
            parts.append(sep)
            parts.append(draw(noise))

        # Maybe open a new span before this word.
        if not open_span and draw(st.booleans()):
            parts.append(draw(sgr_open))
            open_span = True
        elif open_span and draw(st.integers(0, 4)) == 0:
            # Switch style mid-stream (still at word boundary).
            parts.append(draw(sgr_open))

        parts.append(draw(plain_word()))

        # Maybe close after this word.
        if open_span and draw(st.booleans()):
            parts.append(draw(sgr_close))
            open_span = False

    if open_span and draw(st.booleans()):
        parts.append("\x1b[0m")
    return "".join(parts)


widths = st.integers(min_value=8, max_value=120)
indent_widths = st.integers(min_value=0, max_value=8)


def _expected_styled_from_plain_layout(text: str, plain_lines: list[str]):
    """
    Map textwrap's plain layout back onto the original styled character stream.

    Walks non-whitespace content in order; whitespace in the wrapped plain
    lines is not style-checked (textwrap may collapse/replace spaces).
    """
    src = content_chars(text)
    out = []
    idx = 0
    for line in plain_lines:
        for ch in line:
            if ch.isspace():
                continue
            assert idx < len(src), "plain layout consumed more content than styled source"
            sch, style = src[idx]
            assert sch == ch, f"content mismatch at {idx}: {sch!r} vs {ch!r}"
            out.append((ch, style))
            idx += 1
    assert idx == len(src), "styled source has leftover content after plain layout"
    return out


# --- layout properties ------------------------------------------------------


def _words_fit(plain: str, width: int) -> bool:
    """
    Return True if no whitespace-delimited word exceeds ``width``.

    Used to ``assume`` away cases that hit the mid-word
    ``break_long_words`` CSI limitation.
    """
    return all(len(w) <= width for w in plain.split() if w)


@given(text=ansi_text(), width=widths)
@settings(max_examples=80, deadline=None)
def test_layout_matches_textwrap_wrap(text, width):
    """
    Assert ``wrap`` line text matches ``textwrap.wrap`` after stripping CSI.

    Also checks ``ansilen`` equals plain line length. Skips overlong words.
    """
    plain = strip_color(text)
    assume(plain.strip())
    assume(_words_fit(plain, width))
    clean = textwrap.wrap(plain, width)
    colored = wrap(text, width)
    assert [strip_color(line) for line in colored] == clean
    assert [ansilen(line) for line in colored] == [len(line) for line in clean]


@given(text=ansi_text(), width=widths)
@settings(max_examples=80, deadline=None)
def test_layout_matches_textwrap_fill(text, width):
    """
    Assert ``fill`` matches ``textwrap.fill`` on CSI-stripped content.

    Skips empty/whitespace-only inputs and overlong words.
    """
    plain = strip_color(text)
    assume(plain.strip())
    assume(_words_fit(plain, width))
    assert strip_color(fill(text, width)) == textwrap.fill(plain, width)


@given(
    text=ansi_text(),
    width=widths,
    initial=indent_widths,
    subsequent=indent_widths,
)
@settings(max_examples=60, deadline=None)
def test_layout_with_indents(text, width, initial, subsequent):
    """
    Assert unified ``indent=(initial, subsequent)`` matches textwrap indents.

    Requires width greater than both indents and words that fit the content
    column budget.
    """
    plain = strip_color(text)
    assume(plain.strip())
    assume(width > initial and width > subsequent)
    # Content column budget is reduced by the larger indent.
    assume(_words_fit(plain, width - max(initial, subsequent)))
    kw = {
        "initial_indent": " " * initial,
        "subsequent_indent": " " * subsequent,
    }
    clean = textwrap.wrap(plain, width, **kw)
    colored = wrap(text, width, indent=(initial, subsequent))
    assert [strip_color(line) for line in colored] == clean


# --- style / render properties ----------------------------------------------


@given(text=ansi_text(), width=widths)
@settings(max_examples=80, deadline=None)
def test_wrap_preserves_rendered_content_styles(text, width):
    """
    Assert wrap preserves per-character styles on non-whitespace content.

    Compared via the render oracle, independent of CSI spelling or how
    reopen/reset sequences are encoded on each line.
    """
    plain = strip_color(text)
    assume(plain.strip())
    assume(_words_fit(plain, width))
    clean = textwrap.wrap(plain, width)
    assume(clean)
    expected = _expected_styled_from_plain_layout(text, clean)
    actual = content_chars("\n".join(wrap(text, width)))
    assert actual == expected


@given(text=ansi_text(), width=widths)
@settings(max_examples=60, deadline=None)
def test_each_wrapped_line_resets_when_styled(text, width):
    """
    Assert lines that end mid-style terminate with a reset.

    If the last visible character carries a non-default style, playing
    the line in isolation must finish at default style.
    """
    plain = strip_color(text)
    assume(plain.strip())
    assume(_words_fit(plain, width))
    for line in wrap(text, width):
        rendered = styled_chars(line)
        if not rendered:
            continue
        if not rendered[-1][1].is_default():
            assert final_style(line).is_default(), f"line missing reset: {line!r}"


@given(text=ansi_text(max_words=20), width=st.integers(min_value=10, max_value=80))
@settings(max_examples=50, deadline=None)
def test_shorten_preserves_prefix_styles(text, width):
    """
    Assert shorten keeps source styles on the retained content prefix.

    Non-whitespace characters before the placeholder must match the
    corresponding prefix of the original styled content stream.
    """
    plain = " ".join(strip_color(text).strip().split())
    assume(len(plain) > width)
    result = shorten(text, width, placeholder="...")
    plain_result = strip_csi(result)
    assume(plain_result.endswith("..."))
    kept_plain = plain_result[: -len("...")]
    n_kept = sum(1 for ch in kept_plain if not ch.isspace())
    src_content = content_chars(text)
    got = content_chars(result)
    assert got[:n_kept] == src_content[:n_kept]


# --- known limitation (documented, not silently ignored) --------------------


@pytest.mark.xfail(
    reason=(
        "break_long_words slices by raw string index; mid-word CSI makes "
        "visible layout diverge from textwrap on the stripped string. "
        "Width-1 Unicode / wcwidth is a separate future gap."
    ),
    strict=True,
)
def test_known_limitation_midword_csi_break_long_words():
    """
    Document that mid-word CSI breaks layout vs stripped textwrap.

    Strict xfail: ``break_long_words`` slices by raw index, so visible
    breaks diverge when CSI sits between letters of a long word.
    """
    # After strip: 'a aaaaaaaaa' wraps at width 8 to ['a aaaaaa', 'aaa'].
    # With CSI between letters, ansiwrap currently yields different breaks.
    text = "a a" + "".join(f"\x1b[0m{c}" for c in "aaaaaaaaa")
    plain = strip_color(text)
    assert [strip_color(line) for line in wrap(text, 8)] == textwrap.wrap(plain, 8)
