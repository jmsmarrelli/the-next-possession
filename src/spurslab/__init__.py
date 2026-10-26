"""Shared analytics engine for The Next Possession portfolio."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("spurslab")
except PackageNotFoundError:  # pragma: no cover - source checkout before install
    __version__ = "0.1.0"

