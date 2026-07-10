"""Functionality to interact with the terminal."""

import logging
import os
import sys
from contextlib import contextmanager
from re import search
from shutil import get_terminal_size
from types import SimpleNamespace
from typing import Iterator, NamedTuple, cast

from ._tmux import maybe_tmux_escape

# pragma: no cover: start -- platform specific, we always will only execute one branch
if sys.platform == "win32":
    from textual_image._win32 import capture_mode, get_tiocgwinsz, read
else:
    from textual_image._posix import capture_mode, get_tiocgwinsz, read
# pragma: no cover: stop

logger = logging.getLogger(__name__)


# VT340 sizes
FALLBACK_SIZE = (10, 20)


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
    """Get the terminal's character cell size in pixels.

    This function is querying the terminal only once. For any call after the first, a cached result is returned.

    Returns:
        The size information

    """
    if not sys.__stdout__:
        raise TerminalError("stdout is closed")

    if hasattr(get_cell_size, "_result"):
        return cast("CellSize", getattr(get_cell_size, "_result"))

    size = None

    if sys.__stdout__.isatty():
        # Try to get the cell size via ioctl
        try:
            rows, columns, screen_width, screen_height = get_tiocgwinsz()
            width = int(screen_width / columns)
            height = int(screen_height / rows)

            if width and height:
                size = (width, height)
        except OSError as e:
            logger.debug("Failed to get cell size via ioctl, falling back to escape sequence", exc_info=e)

        # Didn't work, let's try to do it via escape sequence
        if not size:
            # CSI 16 t: report character cell size in pixels.
            # Response: ESC [ 6 ; height ; width t
            response = query_tty("\x1b[16t")

            if response and (found := search(r"\x1b\[6;(\d+);(\d+)t", response)):
                height, width = map(int, found.groups())
                size = (width, height)

        # Didn't work, try an alternate escape code sequence
        if not size:
            # CSI 14 t: report terminal dimensions in pixels
            # Response: ESC [ 4 ; pixel_height ; pixel_width t
            response = query_tty("\x1b[14t")

            if response and (found := search(r"\x1b\[4;(\d+);(\d+)t", response)):
                height, width = map(int, found.groups())

                # Note: this can also be done via
                # CSI 18 t response: ESC [ 8 ; rows ; columns t
                # query_tty("\x1b[18t")
                columns, rows = get_terminal_size()

                size = (round(width / columns), round(height / rows))

    # Try environment variables (set by textual-serve for web terminals)
    if not size:
        match os.environ:
            case {
                "TEXTUAL_CELL_WIDTH": str(width_str),
                "TEXTUAL_CELL_HEIGHT": str(height_str),
            } if width_str.isdigit() and height_str.isdigit():
                size = (int(width_str), int(height_str))

    if not size:
        size = FALLBACK_SIZE

    cell_size = CellSize(*size)
    setattr(get_cell_size, "_result", cell_size)
    return cell_size


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
        raise TerminalError("stdin is closed")

    response = SimpleNamespace(sequence="")

    stdin = sys.__stdin__.buffer.fileno()

    with capture_mode():
        yield response

        while not response.sequence.endswith(end_marker):
            response.sequence += read(stdin, 1, timeout)

            if not response.sequence.startswith(start_marker[: len(response.sequence)]):
                raise TerminalError("Unexpected response from terminal")


def query_tty(query: str, timeout: float = 0.1) -> str | None:
    """Query the terminal using an escape code."""
    try:
        with capture_terminal_response("\x1b[", "t", timeout) as response:
            sys.__stdout__.write(query)
            sys.__stdout__.flush()
        return response.sequence
    except (TimeoutError, TerminalError):
        ...


def prepare_terminal_sequence(data: str) -> str:
    return maybe_tmux_escape(data)
