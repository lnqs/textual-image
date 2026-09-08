"""Functionality to interact with the terminal."""

import logging
import os
import re
import sys
from contextlib import contextmanager
from random import randint
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

_PROBE_TIMEOUT = 2.0
_TGP_MESSAGE_START = "\x1b_G"
_TGP_MESSAGE_END = "\x1b\\"
_PRIMARY_DA_RE = re.compile(r"\x1b\[\?[0-9;]*c")
_CELL_SIZE_RE = re.compile(r"\x1b\[6;(\d+);(\d+)t")
_TGP_RESPONSE_RE = re.compile(r"\x1b_G(.*?)\x1b\\", re.DOTALL)


class TerminalError(Exception):
    """Error thrown on failing terminal operations."""

    pass


class CellSize(NamedTuple):
    """Size of terminal cells."""

    width: int
    """Width of a terminal cell in pixels."""
    height: int
    """Height of a terminal cell in pixels."""


class TerminalCapabilities(NamedTuple):
    """Cached results from probing the terminal."""

    cell_size: CellSize
    """Size of a terminal cell in pixels."""
    sixel: bool
    """Whether the terminal reported Sixel support via primary DA."""
    tgp: bool
    """Whether the terminal reported Terminal Graphics Protocol support."""


def get_cell_size() -> CellSize:
    """Get size information from the terminal.

    This function probes the terminal at most once. For any call after the first, a cached result is returned.

    Returns:
        The size information

    """
    return probe_terminal().cell_size


def probe_terminal() -> TerminalCapabilities:
    """Probe the terminal for graphics support and cell size.

    Sends a single batched query (TGP, optional cell-size, primary DA) and parses all replies.
    Primary DA is sent last as a sentinel so non-TGP terminals finish without waiting on silence.
    Results are cached; this must run before Textual takes ownership of stdin.

    Returns:
        Detected terminal capabilities

    Raises:
        TerminalError: If stdout is closed
    """
    if hasattr(probe_terminal, "_result"):
        return cast("TerminalCapabilities", getattr(probe_terminal, "_result"))

    if not sys.__stdout__:
        raise TerminalError("stdout is closed")

    width = 0
    height = 0
    sixel = False
    tgp = False

    if sys.__stdout__.isatty():
        try:
            rows, columns, screen_width, screen_height = get_tiocgwinsz()
            width = int(screen_width / columns)
            height = int(screen_height / rows)
        except OSError as e:
            logger.debug("Failed to get cell size via ioctl, falling back to escape sequence", exc_info=e)

        need_cell_size_query = height == 0 or width == 0

        try:
            with capture_until_primary_da(_PROBE_TIMEOUT) as response:
                sys.__stdout__.write(_tgp_support_query())
                if need_cell_size_query:
                    sys.__stdout__.write("\x1b[16t")
                sys.__stdout__.write("\x1b[c")
                sys.__stdout__.flush()

            sixel, tgp, queried_width, queried_height = _parse_probe_response(response.sequence)
            if need_cell_size_query and queried_width and queried_height:
                width, height = queried_width, queried_height
        except (TerminalError, TimeoutError) as e:
            logger.warning("Failed to probe terminal capabilities", exc_info=e)

    if height == 0 or width == 0:
        # Try environment variables (set by textual-serve for web terminals)
        match os.environ:
            case {
                "TEXTUAL_CELL_WIDTH": str(width_str),
                "TEXTUAL_CELL_HEIGHT": str(height_str),
            } if width_str.isdigit() and height_str.isdigit():
                width = int(width_str)
                height = int(height_str)

    if height == 0 or width == 0:
        # Still didn't work, use VT340 sizes as default
        width = 10
        height = 20

    capabilities = TerminalCapabilities(CellSize(width, height), sixel=sixel, tgp=tgp)
    setattr(probe_terminal, "_result", capabilities)
    return capabilities


def _tgp_support_query() -> str:
    """Build a TGP support query, tmux-escaped when needed."""
    sequence = f"{_TGP_MESSAGE_START}i={randint(1, 2**32)},s=1,v=1,a=q,t=d,f=24;AAAA{_TGP_MESSAGE_END}"
    return prepare_terminal_sequence(sequence)


def _parse_probe_response(sequence: str) -> tuple[bool, bool, int, int]:
    """Parse a batched probe reply buffer.

    Returns:
        sixel supported, tgp supported, cell width, cell height (0 if missing)
    """
    sixel = False
    tgp = False
    width = 0
    height = 0

    da_match = _PRIMARY_DA_RE.search(sequence)
    if da_match:
        params = da_match.group(0)[len("\x1b[?") : -len("c")]
        sixel = "4" in params.split(";")

    for tgp_match in _TGP_RESPONSE_RE.finditer(sequence):
        body = tgp_match.group(1)
        if ";" in body:
            _, status = body.rsplit(";", 1)
            if status == "OK":
                tgp = True
                break

    cell_match = _CELL_SIZE_RE.search(sequence)
    if cell_match:
        height = int(cell_match.group(1))
        width = int(cell_match.group(2))

    return sixel, tgp, width, height


def _has_primary_da(sequence: str) -> bool:
    return _PRIMARY_DA_RE.search(sequence) is not None


@contextmanager
def capture_until_primary_da(timeout: float | None = None) -> Iterator[SimpleNamespace]:
    """Capture terminal replies until a primary DA response arrives.

    Unlike `capture_terminal_response`, this accepts interleaved replies (TGP, cell size, DA)
    and stops when primary DA (`CSI ? ... c`) is present.

    Please not this function will not work anymore once Textual is started. Textual runs a threads to read stdin
    and will grab the response.

    Args:
        timeout: Seconds to wait per read. None to disable timeout.

    Yields:
        A namespace with a `sequence` attribute filled after the context body runs
    """
    if not sys.__stdin__:
        raise TerminalError("stdin is closed")

    response = SimpleNamespace(sequence="")
    stdin = sys.__stdin__.buffer.fileno()

    with capture_mode():
        yield response

        while not _has_primary_da(response.sequence):
            response.sequence += read(stdin, 1, timeout)


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


def prepare_terminal_sequence(data: str) -> str:
    return maybe_tmux_escape(data)
