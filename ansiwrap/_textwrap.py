"""
Private stdlib textwrap loaded for ANSI-aware ``len`` monkey-patching.

Strategy
--------
At import time this module loads the host interpreter's ``textwrap`` source
and ``exec``s it into this module's globals. ``ansiwrap.core`` then patches
``len`` on *this* copy only (never the real stdlib module).

Why load the live stdlib module (positives)
-------------------------------------------
- Zero runtime dependencies (no ``textwrap3`` or vendored snapshot to maintain).
- Best possible fidelity to the current interpreter's ``textwrap``: wrap /
  fill / shorten semantics, including incidental quirks and bug-compatibility
  with that Python version.
- As CPython/PyPy evolve ``textwrap`` across the supported range (3.10+),
  ansiwrap tracks those changes automatically instead of freezing an old
  algorithm.

Tradeoffs
---------
- Behavior can differ slightly across Python versions (by design: we mirror
  whatever ``textwrap`` the host ships).
- Import-time filesystem read + ``exec`` is less auditable and less
  type-checker friendly than a pinned private copy or a ``TextWrapper``
  subclass.
- We do not pin "exact wrap algorithm forever"; reproducibility across
  interpreters is "same as that interpreter's textwrap," not "byte-identical
  to a frozen snapshot."

User-facing documentation of this choice is planned later (see
``EVOLUTION.md``).
"""

from __future__ import annotations

import importlib.util
import pathlib

_spec = importlib.util.find_spec("textwrap")
if _spec is None or _spec.origin is None:  # pragma: no cover
    raise ImportError("stdlib textwrap not found")
exec(compile(pathlib.Path(_spec.origin).read_text(encoding="utf-8"), _spec.origin, "exec"), globals())
