from array import array
from typing import IO
from unittest.mock import patch

from pytest import raises

from tests.data import TERM_SIZE, TERM_SIZE_NO_SCREEN
from textual_kitty.terminal import TerminalError, get_terminal_size_info


def test_get_terminal_size_info_on_tty_success() -> None:
    def ioctl(fd: IO[bytes], request: int, buf: array[int]) -> None:
        buf[0], buf[1], buf[2], buf[3], _, _ = TERM_SIZE

    with patch("sys.__stdout__.isatty", return_value=True):
        with patch("textual_kitty.terminal.ioctl", side_effect=ioctl):
            assert get_terminal_size_info() == TERM_SIZE


def test_get_terminal_size_info_on_tty_no_screen_size() -> None:
    def ioctl(fd: IO[bytes], request: int, buf: array[int]) -> None:
        buf[0], buf[1], buf[2], buf[3], _, _ = TERM_SIZE_NO_SCREEN

    with patch("sys.__stdout__.isatty", return_value=True):
        with patch("textual_kitty.terminal.ioctl", side_effect=ioctl):
            assert get_terminal_size_info() == TERM_SIZE_NO_SCREEN


def test_get_terminal_size_info_on_tty_failure() -> None:
    with patch("sys.__stdout__.isatty", return_value=True):
        with patch("textual_kitty.terminal.ioctl", side_effect=OSError()):
            with raises(TerminalError):
                get_terminal_size_info()


def test_get_terminal_size_info_stdout_closed() -> None:
    with patch("sys.__stdout__", None):
        with raises(TerminalError):
            get_terminal_size_info()


def test_get_terminal_size_info_stdout_not_a_tty() -> None:
    with patch("sys.__stdout__.isatty", return_value=False):
        term_size = get_terminal_size_info()

    assert term_size.screen_width == 0
    assert term_size.screen_height == 0
