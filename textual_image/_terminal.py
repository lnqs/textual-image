"""Functionality to interact with the terminal."""

import logging
import os
import sys
import termios
import tty
from array import array
from contextlib import contextmanager
from fcntl import ioctl
from select import select
from types import SimpleNamespace
from typing import Iterator, NamedTuple

logger = logging.getLogger(__name__)


class TerminalError(Exception):
    """Error thrown on failing terminal operations."""

    pass


class CellSize(NamedTuple):
    """Size of terminal cells."""

    width: int
    """Width of a terminal cell in pixels."""
    height: int
    """Height of a terminal cell in pixels."""


def get_cell_size() -> CellSize:
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
    cell_height = int(screen_height / rows) or 16

    return CellSize(cell_width, cell_height)


@contextmanager
def capture_terminal_response(
    start_marker: str, end_marker: str, timeout: float | None = None
) -> Iterator[SimpleNamespace]:
    """Captures a terminal response.

    Captures the terminal's response to an escape sequence.
    This is a bit flaky -- keystrokes during reading the response can lead to false answers.
    Additionally, when the terminal does *not* doesn't send an answer, the first character
    of stdin may get lost as this function reads it to determine if it is the response.
    Anyway, as this is improbable to happen, it should be fine.

    Please not this function will not work anymore once Textual is started. Textual runs a threads to read stdin
    and will grab the response.

    Args:
        start_marker: The start sequence of the expected response
        end_marker: The end sequence of the expected response
        timeout: The number of seconds to wait for the response. None to disable timeout.

    Returns:
        The terminal's response
    """
    if not sys.__stdin__:
        raise TerminalError("stdout is closed")

    response = SimpleNamespace(sequence="")

    stdin = sys.__stdin__.buffer.fileno()
    old_term_mode = termios.tcgetattr(stdin)
    tty.setcbreak(stdin, termios.TCSANOW)

    try:
        yield response

        while not response.sequence.endswith(end_marker):
            readable, _, _ = select([stdin], [], [], timeout)
            if not readable:
                raise TimeoutError("Timeout waiting for response")

            response.sequence += os.read(stdin, 1).decode()

            if not response.sequence.startswith(start_marker[: len(response.sequence)]):
                raise TerminalError("Unexpected response from terminal")

    finally:
        termios.tcsetattr(stdin, termios.TCSANOW, old_term_mode)
