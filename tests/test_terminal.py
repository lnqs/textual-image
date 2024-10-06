import sys
from array import array
from contextlib import contextmanager
from types import SimpleNamespace
from typing import IO, Iterator
from unittest.mock import patch

from pytest import raises

from textual_image._terminal import TerminalError, capture_terminal_response, get_cell_size

if sys.version_info >= (3, 12):
    IntArray = array[int]
else:
    IntArray = array


def test_get_cell_size_stdout_closed() -> None:
    with patch("sys.__stdout__", None):
        with raises(TerminalError):
            get_cell_size()


def test_get_cell_size_on_tty_ioctl_success() -> None:
    if hasattr(get_cell_size, "_result"):
        delattr(get_cell_size, "_result")

    def ioctl(fd: IO[bytes], request: int, buf: IntArray) -> None:
        buf[0] = 58
        buf[1] = 120
        buf[2] = 960
        buf[3] = 928

    with patch("sys.__stdout__.isatty", return_value=True):
        with patch("textual_image._terminal.ioctl", ioctl):
            assert get_cell_size() == (8, 16)


def test_get_cell_size_on_tty_escape_sequence() -> None:
    if hasattr(get_cell_size, "_result"):
        delattr(get_cell_size, "_result")

    @contextmanager
    def capture_terminal_response(
        start_marker: str, end_marker: str, timeout: float | None = None
    ) -> Iterator[SimpleNamespace]:
        yield SimpleNamespace(sequence="\x1b[6;8;16t")

    with patch("sys.__stdout__.isatty", return_value=True):
        with patch("textual_image._terminal.ioctl", side_effect=OSError()):
            with patch("textual_image._terminal.capture_terminal_response", capture_terminal_response):
                get_cell_size()


def test_get_cell_size_on_tty_failure() -> None:
    if hasattr(get_cell_size, "_result"):
        delattr(get_cell_size, "_result")

    @contextmanager
    def capture_terminal_response(
        start_marker: str, end_marker: str, timeout: float | None = None
    ) -> Iterator[SimpleNamespace]:
        raise TimeoutError()

    with patch("sys.__stdout__.isatty", return_value=True):
        with patch("textual_image._terminal.ioctl", side_effect=OSError()):
            with patch("textual_image._terminal.capture_terminal_response", capture_terminal_response):
                with raises(TerminalError):
                    get_cell_size()


def test_get_cell_size_stdout_not_a_tty() -> None:
    if hasattr(get_cell_size, "_result"):
        delattr(get_cell_size, "_result")

    with patch("sys.__stdout__.isatty", return_value=False):
        term_size = get_cell_size()

    assert term_size.width == 10
    assert term_size.height == 20


def test_capture_terminal_response() -> None:
    with patch("sys.__stdin__", None):
        with raises(TerminalError):
            with capture_terminal_response("[S]", "[E]") as response:
                pass

    with patch("sys.__stdin__") as stdin, patch("termios.tcgetattr"), patch("termios.tcsetattr"), patch(
        "tty.setcbreak"
    ), patch("textual_image._terminal.select") as select, patch("os.read") as read:
        stdin.buffer.fileno.return_value = 42
        select.return_value = [[42], [], []]
        read.side_effect = [c.to_bytes(1, sys.byteorder) for c in b"[S]message[E]"]

        with capture_terminal_response("[S]", "[E]") as response:
            pass

        assert response.sequence == "[S]message[E]"

    with patch("sys.__stdin__") as stdin, patch("termios.tcgetattr"), patch("termios.tcsetattr"), patch(
        "tty.setcbreak"
    ), patch("textual_image._terminal.select") as select:
        stdin.buffer.fileno.return_value = 42
        select.return_value = [[], [], []]

        with raises(TimeoutError):
            with capture_terminal_response("[S]", "[E]") as response:
                pass

    with patch("sys.__stdin__") as stdin, patch("termios.tcgetattr"), patch("termios.tcsetattr"), patch(
        "tty.setcbreak"
    ), patch("textual_image._terminal.select") as select, patch("os.read") as read:
        stdin.buffer.fileno.return_value = 42
        select.return_value = [[42], [], []]
        read.side_effect = [c.to_bytes(1, sys.byteorder) for c in b"not the expected message"]

        with raises(TerminalError):
            with capture_terminal_response("[S]", "[E]") as response:
                pass
