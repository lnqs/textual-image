"""Functionality to interact with the terminal."""

import logging
import sys
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Iterator, NamedTuple, cast

# pragma: no cover: start -- platform specific, we always will only execute one branch
if sys.platform == "win32":
    from textual_image._win32 import capture_mode, get_tiocgwinsz, read
else:
    from textual_image._posix import capture_mode, get_tiocgwinsz, read
# pragma: no cover: stop

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

    This function is querying the terminal only once. For any call after the first, a cached result is returned.

    Returns:
        The size information

    """
    if not sys.__stdout__:
        raise TerminalError("stdout is closed")

    if hasattr(get_cell_size, "_result"):
        return cast(CellSize, get_cell_size._result)

    width = 0
    height = 0

    if sys.__stdout__.isatty():
        # Try to get the cell size via ioctl
        try:
            rows, columns, screen_width, screen_height = get_tiocgwinsz()
            width = int(screen_width / columns)
            height = int(screen_height / rows)
        except OSError:
            logger.debug("Failed to get cell size via ioctl, falling back to escape sequence")

    if sys.__stdout__.isatty() and (height == 0 or width == 0):
        # Didn't work, let's try to do it via escape sequence
        try:
            with capture_terminal_response("\x1b[", "t", 0.1) as response:
                sys.__stdout__.write("\x1b[16t")
                sys.__stdout__.flush()

            sequence = response.sequence[len("\x1b[") : -len("t")]
            _, height, width = [int(v) for v in sequence.split(";")]
        except (TerminalError, TimeoutError) as e:
            raise TerminalError("Failed to get cell size") from e

    if not sys.__stdout__.isatty():
        logger.debug("Not connected to a terminal, assuming VT340 sizes")
        width = 10
        height = 20

    cell_size = CellSize(width, height)
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
