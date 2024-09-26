from array import array
from typing import IO
from unittest.mock import patch

from pytest import raises

from tests.data import TERMINAL_SIZES
from textual_kitty.terminal import TerminalError, TerminalSizes, capture_terminal_response, get_terminal_sizes


def test_get_terminal_sizes_on_tty_success() -> None:
    def ioctl(fd: IO[bytes], request: int, buf: array[int]) -> None:
        buf[0], buf[1], buf[2], buf[3], _, _ = TERMINAL_SIZES

    with patch("sys.__stdout__.isatty", return_value=True):
        with patch("textual_kitty.terminal.ioctl", side_effect=ioctl):
            assert get_terminal_sizes() == TERMINAL_SIZES


def test_get_terminal_sizes_on_tty_no_screen_size() -> None:
    terminal_sizes = TerminalSizes(
        rows=TERMINAL_SIZES.rows,
        columns=TERMINAL_SIZES.columns,
        screen_width=0,
        screen_height=0,
        cell_width=TERMINAL_SIZES.cell_width,
        cell_height=TERMINAL_SIZES.cell_height,
    )

    def ioctl(fd: IO[bytes], request: int, buf: array[int]) -> None:
        buf[0], buf[1], buf[2], buf[3], _, _ = terminal_sizes

    with patch("sys.__stdout__.isatty", return_value=True):
        with patch("textual_kitty.terminal.ioctl", side_effect=ioctl):
            assert get_terminal_sizes() == terminal_sizes


def test_get_terminal_sizes_on_tty_failure() -> None:
    with patch("sys.__stdout__.isatty", return_value=True):
        with patch("textual_kitty.terminal.ioctl", side_effect=OSError()):
            with raises(TerminalError):
                get_terminal_sizes()


def test_get_terminal_sizes_stdout_closed() -> None:
    with patch("sys.__stdout__", None):
        with raises(TerminalError):
            get_terminal_sizes()


def test_get_terminal_sizes_stdout_not_a_tty() -> None:
    with patch("sys.__stdout__.isatty", return_value=False):
        term_size = get_terminal_sizes()

    assert term_size.screen_width == 0
    assert term_size.screen_height == 0


def test_capture_terminal_response() -> None:
    with patch("sys.__stdin__", None):
        with raises(TerminalError):
            with capture_terminal_response("[S]", "[E]") as response:
                pass

    with patch("sys.__stdin__") as stdin, patch("termios.tcgetattr"), patch("termios.tcsetattr"), patch(
        "tty.setcbreak"
    ), patch("textual_kitty.terminal.select") as select, patch("os.read") as read:
        stdin.buffer.fileno.return_value = 42
        select.return_value = [[42], [], []]
        read.side_effect = [c.to_bytes() for c in b"[S]message[E]"]

        with capture_terminal_response("[S]", "[E]") as response:
            pass

        assert response.sequence == "[S]message[E]"

    with patch("sys.__stdin__") as stdin, patch("termios.tcgetattr"), patch("termios.tcsetattr"), patch(
        "tty.setcbreak"
    ), patch("textual_kitty.terminal.select") as select:
        stdin.buffer.fileno.return_value = 42
        select.return_value = [[], [], []]

        with raises(TimeoutError):
            with capture_terminal_response("[S]", "[E]") as response:
                pass

    with patch("sys.__stdin__") as stdin, patch("termios.tcgetattr"), patch("termios.tcsetattr"), patch(
        "tty.setcbreak"
    ), patch("textual_kitty.terminal.select") as select, patch("os.read") as read:
        stdin.buffer.fileno.return_value = 42
        select.return_value = [[42], [], []]
        read.side_effect = [c.to_bytes() for c in b"not the expected message"]

        with raises(TerminalError):
            with capture_terminal_response("[S]", "[E]") as response:
                pass
