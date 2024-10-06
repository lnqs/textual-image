# pragma: exclude file -- this is platform specific code, either this or _posix.py won't get tested,
# depending on the platform the tests are running

import ctypes
import msvcrt
import os
import sys
from contextlib import contextmanager
from ctypes.wintypes import DWORD
from typing import Iterator, Tuple

kernel32 = ctypes.WinDLL("kernel32")  # type: ignore


class Win32TerminalError(Exception):
    """Error thrown on failing terminal operations."""

    pass


def get_tiocgwinsz() -> Tuple[int, int, int, int]:
    raise OSError("TIOCGWINSZ not supported on Windows")


def read(fd: int, length: int, timeout: float | None = None) -> str:
    if timeout is not None:
        wait_for_object(fd, timeout)
    return os.read(fd, length).decode()


@contextmanager
def capture_mode() -> Iterator[None]:
    if not sys.__stdin__:
        raise Win32TerminalError("stdout is closed")

    stdin = sys.stdin.buffer.fileno()

    original_mode = get_console_mode(stdin)
    set_console_mode(stdin, 0x0200)  # ENABLE_VIRTUAL_TERMINAL_INPUT

    try:
        flush(stdin)
        yield
    finally:
        set_console_mode(stdin, original_mode)


def wait_for_object(fd: int, timeout: float) -> None:
    handle = msvcrt.get_osfhandle(fd)  # type: ignore
    ret: int = kernel32.WaitForSingleObject(handle, DWORD(int(timeout * 1000)))
    if ret == 0x00000102:  # WAIT_TIMEOUT
        raise TimeoutError("Timeout waiting for data")


def get_console_mode(fd: int) -> int:
    handle = msvcrt.get_osfhandle(fd)  # type: ignore
    mode = DWORD()
    kernel32.GetConsoleMode(handle, ctypes.byref(mode))
    return mode.value


def set_console_mode(fd: int, mode: int) -> None:
    handle = msvcrt.get_osfhandle(fd)  # type: ignore
    kernel32.SetConsoleMode(handle, mode)


def flush(fd: int) -> None:
    handle = msvcrt.get_osfhandle(fd)  # type: ignore
    kernel32.FlushConsoleInputBuffer(handle)
