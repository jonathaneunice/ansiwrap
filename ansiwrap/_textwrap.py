"""
Private stdlib textwrap copy for ANSI-aware len monkey-patching.
"""

from __future__ import annotations

import importlib.util
import pathlib

_spec = importlib.util.find_spec("textwrap")
if _spec is None or _spec.origin is None:  # pragma: no cover
    raise ImportError("stdlib textwrap not found")
exec(compile(pathlib.Path(_spec.origin).read_text(encoding="utf-8"), _spec.origin, "exec"), globals())
