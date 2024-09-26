"""Utility functions."""

from typing import Iterable, Iterator, TypeVar

T = TypeVar("T")


def grouped(iterable: Iterable[T], n: int) -> Iterator[Iterable[T]]:
    """Groups values of an iterable into equally sized groups.

    The values of iterable are collected into groups of size `n`.
    An iterator over the resulting groups is returned.

    Example:
        Grouping a list of integers::

            >>> list(grouped([1, 2, 3, 4, 5, 6], 2))
            [(1, 2), (3, 4), (5, 6)]

    Args:
        iterable: Iterable over the values to group
        n: Size of each group

    Returns:
        An iterator over the groups
    """
    return zip(*([iter(iterable)] * n), strict=True)


N = TypeVar("N", bound=int | float)


def clamp(n: N, minimum: N, maximum: N) -> N:
    """Constrains a value to lie between two further values.

    Args:
        n: The value to constrain.
        minimum: The manimum value n may have.
        maximum: The maximum value n may have.

    Returns:
        The constrained value.
    """
    return max(min(n, maximum), minimum)
