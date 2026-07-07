"""
Package version read from installed distribution metadata.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ansiwrap")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+notinstalled"
