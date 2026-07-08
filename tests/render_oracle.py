"""
Independent SGR render oracle for content-level tests.

Walks a string, tracks graphic rendition state, and yields visible
characters paired with a normalized style. Used to compare wrap/fill
output by rendered appearance rather than exact CSI byte spelling.

Display-width note
------------------
ansiwrap (like textwrap) measures visible length with Python ``len()``
after stripping CSI sequences. That treats every Unicode code point as
width 1. East Asian wide characters, emoji, and combining marks are
therefore out of scope for these oracles until the library grows a
wcwidth-aware path. Generators should stick to width-1 code points.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Same practical CSI subset ansiwrap recognizes (SGR + EL).
_ANSI_RE = re.compile(r"\x1b\[(K|.*?m)")


@dataclass(frozen=True)
class Style:
    """
    Normalized graphic rendition.

    Equality of ``Style`` values is the render oracle's comparison key,
    independent of how CSI sequences were originally spelled.
    """

    fg: tuple[int, ...] | None = None
    bg: tuple[int, ...] | None = None
    attrs: frozenset[int] = frozenset()

    def is_default(self) -> bool:
        """
        Return True when no foreground, background, or attrs are set.

        That is the terminal's default graphic rendition.
        """
        return self.fg is None and self.bg is None and not self.attrs


def apply_sgr(style: Style, params: list[int]) -> Style:
    """
    Return a new ``Style`` after applying SGR parameter list ``params``.

    Unrecognized parameters are ignored, matching ansiwrap's parser.
    Invalid 38/48 color modes raise ``ValueError``.
    """
    fg, bg = style.fg, style.bg
    attrs = set(style.attrs)
    vals = list(params)
    while vals:
        top = vals.pop(0)
        if top == 0:
            fg = bg = None
            attrs.clear()
        elif 1 <= top <= 9:
            attrs.add(top)
        elif 21 <= top <= 29:
            attrs.discard(top - 20)
        elif 30 <= top <= 37 or 90 <= top <= 97:
            # Standard and bright/aixterm foreground.
            fg = (top,)
        elif top == 39:
            fg = None
        elif top == 38:
            under = vals.pop(0)
            if under == 5:
                fg = (38, 5, vals.pop(0))
            elif under == 2:
                fg = (38, 2, vals.pop(0), vals.pop(0), vals.pop(0))
            else:
                raise ValueError(f"unsupported fg color mode {under}")
        elif 40 <= top <= 47 or 100 <= top <= 107:
            # Standard and bright/aixterm background.
            bg = (top,)
        elif top == 49:
            bg = None
        elif top == 48:
            under = vals.pop(0)
            if under == 5:
                bg = (48, 5, vals.pop(0))
            elif under == 2:
                bg = (48, 2, vals.pop(0), vals.pop(0), vals.pop(0))
            else:
                raise ValueError(f"unsupported bg color mode {under}")
        # Unrecognized parameters (e.g. 99) are ignored, matching ansiwrap.
    return Style(fg=fg, bg=bg, attrs=frozenset(attrs))


def _sgr_params(body: str) -> list[int] | None:
    """
    Return SGR params for a CSI body, or None if not an SGR sequence.

    ``body`` is the text inside ``ESC[`` ... (e.g. ``31m`` or ``K``).
    Bare ``m`` is treated as reset (``[0]``).
    """
    if body == "K" or not body.endswith("m"):
        return None
    raw = body[:-1]
    return [0] if raw == "" else [int(p or 0) for p in raw.split(";")]


def final_style(s: str) -> Style:
    """
    Return the style in effect after playing every CSI sequence in ``s``.

    Visible characters are ignored; only escape sequences update state.
    """
    style = Style()
    for match in _ANSI_RE.finditer(s):
        params = _sgr_params(match.group(1))
        if params is not None:
            style = apply_sgr(style, params)
    return style


def styled_chars(s: str) -> list[tuple[str, Style]]:
    """
    Render ``s`` to a list of (visible_char, style) pairs.

    CSI sequences are not emitted; only their effect on subsequent
    characters is. Non-SGR ``\\x1b[K`` is skipped with no state change.
    """
    out: list[tuple[str, Style]] = []
    style = Style()
    pos = 0
    for match in _ANSI_RE.finditer(s):
        if match.start() > pos:
            for ch in s[pos : match.start()]:
                out.append((ch, style))
        params = _sgr_params(match.group(1))
        if params is not None:
            style = apply_sgr(style, params)
        pos = match.end()
    if pos < len(s):
        for ch in s[pos:]:
            out.append((ch, style))
    return out


def content_chars(s: str) -> list[tuple[str, Style]]:
    """
    Return visible non-whitespace characters with their styles.

    Order is preserved. Useful when comparing wrap output to a source
    stream without caring how textwrap collapsed whitespace.
    """
    return [(ch, st) for ch, st in styled_chars(s) if not ch.isspace()]


def strip_csi(s: str) -> str:
    """
    Remove CSI sequences recognized by the oracle from ``s``.

    Same practical subset as ansiwrap (SGR and erase-line).
    """
    return _ANSI_RE.sub("", s)
