"""Geometry data structures."""

from typing import NamedTuple


class Size(NamedTuple):
    """The dimensions (width and height) of a rectangular region."""

    width: int
    """The width."""
    height: int
    """The height."""
