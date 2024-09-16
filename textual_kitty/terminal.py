"""Functionality to interact with the terminal."""

import logging
import sys
import termios
from array import array
from fcntl import ioctl
from typing import NamedTuple

logger = logging.getLogger(__name__)


class TerminalError(Exception):
    """Error thrown on failing terminal operations."""

    pass


class TerminalSizeInformation(NamedTuple):
    """Size of several terminal features."""

    rows: int
    """Width of the terminal in cells."""
    columns: int
    """Height of the terminal in cells."""
    screen_width: int
    """Width of the terminal in pixels."""
    screen_height: int
    """Height of the terminal in pixels."""
    cell_width: int
    """Width of a terminal cell in pixels."""
    cell_height: int
    """Height of a terminal cell in pixels."""


def get_terminal_size_info() -> TerminalSizeInformation:
    """Get size information from the terminal.

    Returns:
        The size information

    """
    if not sys.__stdout__:
        raise TerminalError("stdout is closed")

    if sys.__stdout__.isatty():
        try:
            buf = array("H", [0, 0, 0, 0])
            ioctl(sys.__stdout__, termios.TIOCGWINSZ, buf)

            rows, columns, screen_width, screen_height = buf

            # If we can't get the cell size (not all terminals support this) we're just assuming some hopefully reasonable numbers.
            # Does this suck? Yes. Is there something we can do about it? Not really.
            if not screen_width or not screen_height:
                logger.warning("Terminal doesn't support getting pixel size; falling back to assumptions")

        except OSError as e:
            raise TerminalError("Unsupported terminal") from e

    else:
        logger.debug("Not connected to a terminal, assuming reasonable size information")
        rows = 24
        columns = 80
        screen_width = 0
        screen_height = 0

    cell_width = int(screen_width / columns) or 8
    cell_height = int(screen_height / rows) or 12

    return TerminalSizeInformation(
        rows=rows,
        columns=columns,
        screen_width=screen_width,
        screen_height=screen_height,
        cell_width=cell_width,
        cell_height=cell_height,
    )
