# pragma: exclude file -- this is platform specific code, either this or _win32.py won't get tested,
# depending on the platform the tests are running

import os
import sys
import termios
import tty
from array import array
from contextlib import contextmanager
from fcntl import ioctl  # type: ignore
from select import select
from typing import Iterator, Tuple


class PosixTerminalError(Exception):
    """Error thrown on failing terminal operations."""

    pass


def get_tiocgwinsz() -> Tuple[int, int, int, int]:
    if not sys.__stdout__:
        raise PosixTerminalError("stdout is closed")

    buf = array("H", [0, 0, 0, 0])
    ioctl(sys.__stdout__, termios.TIOCGWINSZ, buf)  # type: ignore
    rows, columns, screen_width, screen_height = buf
    return rows, columns, screen_width, screen_height


def read(fd: int, length: int, timeout: float | None = None) -> str:
    readable, _, _ = select([fd], [], [], timeout)
    if not readable:
        raise TimeoutError("Timeout waiting for data")
    return os.read(fd, length).decode()


@contextmanager
def capture_mode() -> Iterator[None]:
    if not sys.__stdin__:
        raise PosixTerminalError("stdout is closed")

    stdin = sys.__stdin__.buffer.fileno()
    original_mode = termios.tcgetattr(stdin)  # type: ignore
    tty.setcbreak(stdin, termios.TCSANOW)  # type: ignore

    try:
        yield
    finally:
        termios.tcsetattr(stdin, termios.TCSANOW, original_mode)  # type: ignore
