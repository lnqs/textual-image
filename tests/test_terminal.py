import sys
from array import array
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Iterator
from unittest.mock import MagicMock, patch

from pytest import raises

from textual_image._terminal import (
    TerminalCapabilities,
    TerminalError,
    capture_terminal_response,
    capture_until_primary_da,
    get_cell_size,
    probe_terminal,
)

if sys.version_info >= (3, 12):
    IntArray = array[int]
else:
    IntArray = array


def _clear_probe_cache() -> None:
    if hasattr(probe_terminal, "_result"):
        delattr(probe_terminal, "_result")


def test_get_cell_size_stdout_closed() -> None:
    _clear_probe_cache()
    with patch("sys.__stdout__", None):
        with raises(TerminalError):
            get_cell_size()


def test_get_cell_size_on_tty_ioctl_success() -> None:
    _clear_probe_cache()

    @contextmanager
    def capture_da(timeout: float | None = None) -> Iterator[SimpleNamespace]:
        yield SimpleNamespace(sequence="\x1b[?62c")

    with patch("sys.__stdout__") as stdout:
        stdout.isatty.return_value = True
        with patch("textual_image._terminal.get_tiocgwinsz", return_value=(58, 120, 960, 928)):
            with patch("textual_image._terminal.capture_until_primary_da", capture_da):
                assert get_cell_size() == (8, 16)


def test_get_cell_size_on_tty_escape_sequence() -> None:
    _clear_probe_cache()

    @contextmanager
    def capture_da(timeout: float | None = None) -> Iterator[SimpleNamespace]:
        yield SimpleNamespace(sequence="\x1b[6;8;16t\x1b[?62c")

    with patch("sys.__stdout__") as stdout:
        stdout.isatty.return_value = True
        with patch("textual_image._terminal.get_tiocgwinsz", side_effect=OSError()):
            with patch("textual_image._terminal.capture_until_primary_da", capture_da):
                assert get_cell_size() == (16, 8)


def test_get_cell_size_on_tty_failure() -> None:
    _clear_probe_cache()

    @contextmanager
    def capture_da(timeout: float | None = None) -> Iterator[SimpleNamespace]:
        raise TimeoutError()

    with patch("sys.__stdout__") as stdout:
        stdout.isatty.return_value = True
        with patch("textual_image._terminal.get_tiocgwinsz", side_effect=OSError()):
            with patch("textual_image._terminal.capture_until_primary_da", capture_da):
                assert get_cell_size() == (10, 20)


def test_get_cell_size_env_variable_fallback() -> None:
    _clear_probe_cache()

    @contextmanager
    def capture_da(timeout: float | None = None) -> Iterator[SimpleNamespace]:
        raise TimeoutError()

    env = {"TEXTUAL_CELL_WIDTH": "12", "TEXTUAL_CELL_HEIGHT": "24"}
    with patch("sys.__stdout__") as stdout:
        stdout.isatty.return_value = True
        with patch("textual_image._terminal.get_tiocgwinsz", side_effect=OSError()):
            with patch("textual_image._terminal.capture_until_primary_da", capture_da):
                with patch.dict("os.environ", env, clear=True):
                    result = get_cell_size()

    assert result.width == 12
    assert result.height == 24


def test_get_cell_size_stdout_not_a_tty() -> None:
    _clear_probe_cache()

    with patch("sys.__stdout__") as stdout:
        stdout.isatty.return_value = False
        term_size = get_cell_size()

    assert term_size.width == 10
    assert term_size.height == 20


def test_probe_terminal_sixel_and_tgp() -> None:
    _clear_probe_cache()

    @contextmanager
    def capture_da(timeout: float | None = None) -> Iterator[SimpleNamespace]:
        yield SimpleNamespace(sequence="\x1b_Gd=1;OK\x1b\\\x1b[?62;4c")

    written: list[str] = []

    def write(data: str) -> int:
        written.append(data)
        return len(data)

    with patch("sys.__stdout__") as stdout:
        stdout.isatty.return_value = True
        stdout.write.side_effect = write
        with patch("textual_image._terminal.get_tiocgwinsz", return_value=(58, 120, 960, 928)):
            with patch("textual_image._terminal.capture_until_primary_da", capture_da):
                caps = probe_terminal()

    assert caps == TerminalCapabilities(cell_size=caps.cell_size, sixel=True, tgp=True)
    assert caps.cell_size == (8, 16)
    assert any("a=q" in part for part in written)
    assert "\x1b[c" in written
    assert not any("\x1b[16t" in part for part in written)


def test_probe_terminal_da_only_no_sixel() -> None:
    _clear_probe_cache()

    @contextmanager
    def capture_da(timeout: float | None = None) -> Iterator[SimpleNamespace]:
        yield SimpleNamespace(sequence="\x1b[?62c")

    with patch("sys.__stdout__") as stdout:
        stdout.isatty.return_value = True
        with patch("textual_image._terminal.get_tiocgwinsz", return_value=(58, 120, 960, 928)):
            with patch("textual_image._terminal.capture_until_primary_da", capture_da):
                caps = probe_terminal()

    assert caps.sixel is False
    assert caps.tgp is False


def test_probe_terminal_queries_cell_size_when_ioctl_fails() -> None:
    _clear_probe_cache()

    @contextmanager
    def capture_da(timeout: float | None = None) -> Iterator[SimpleNamespace]:
        yield SimpleNamespace(sequence="\x1b[6;20;10t\x1b[?1;2;3;4c")

    written: list[str] = []

    def write(data: str) -> int:
        written.append(data)
        return len(data)

    with patch("sys.__stdout__") as stdout:
        stdout.isatty.return_value = True
        stdout.write.side_effect = write
        with patch("textual_image._terminal.get_tiocgwinsz", side_effect=OSError()):
            with patch("textual_image._terminal.capture_until_primary_da", capture_da):
                caps = probe_terminal()

    assert caps.cell_size == (10, 20)
    assert caps.sixel is True
    assert "\x1b[16t" in written
    assert "\x1b[c" in written


def test_probe_terminal_all_three_replies() -> None:
    _clear_probe_cache()

    @contextmanager
    def capture_da(timeout: float | None = None) -> Iterator[SimpleNamespace]:
        yield SimpleNamespace(sequence="\x1b_Gx=1;OK\x1b\\\x1b[6;14;7t\x1b[?62;4c")

    with patch("sys.__stdout__") as stdout:
        stdout.isatty.return_value = True
        with patch("textual_image._terminal.get_tiocgwinsz", side_effect=OSError()):
            with patch("textual_image._terminal.capture_until_primary_da", capture_da):
                caps = probe_terminal()

    assert caps.tgp is True
    assert caps.sixel is True
    assert caps.cell_size == (7, 14)


def test_probe_terminal_tgp_failure_status() -> None:
    _clear_probe_cache()

    @contextmanager
    def capture_da(timeout: float | None = None) -> Iterator[SimpleNamespace]:
        yield SimpleNamespace(sequence="\x1b_Gd=1;FAIL\x1b\\\x1b[?62c")

    with patch("sys.__stdout__") as stdout:
        stdout.isatty.return_value = True
        with patch("textual_image._terminal.get_tiocgwinsz", return_value=(58, 120, 960, 928)):
            with patch("textual_image._terminal.capture_until_primary_da", capture_da):
                caps = probe_terminal()

    assert caps.tgp is False


def test_probe_terminal_caches_result() -> None:
    _clear_probe_cache()

    calls = 0

    @contextmanager
    def capture_da(timeout: float | None = None) -> Iterator[SimpleNamespace]:
        nonlocal calls
        calls += 1
        yield SimpleNamespace(sequence="\x1b[?62;4c")

    with patch("sys.__stdout__") as stdout:
        stdout.isatty.return_value = True
        with patch("textual_image._terminal.get_tiocgwinsz", return_value=(58, 120, 960, 928)):
            with patch("textual_image._terminal.capture_until_primary_da", capture_da):
                first = probe_terminal()
                second = probe_terminal()

    assert first is second
    assert calls == 1


def test_capture_until_primary_da_success() -> None:
    with patch("sys.__stdin__", MagicMock()):
        with patch("textual_image._terminal.capture_mode"):
            with patch("textual_image._terminal.read", side_effect=list("\x1b_GOK\x1b\\\x1b[?62;4c")):
                with capture_until_primary_da() as response:
                    pass

            assert response.sequence == "\x1b_GOK\x1b\\\x1b[?62;4c"


def test_capture_until_primary_da_timeout() -> None:
    with patch("sys.__stdin__", MagicMock()):
        with patch("textual_image._terminal.capture_mode"):
            with patch("textual_image._terminal.read", side_effect=TimeoutError()):
                with raises(TimeoutError):
                    with capture_until_primary_da():
                        pass


def test_capture_until_primary_da_stdin_closed() -> None:
    with patch("sys.__stdin__", None):
        with raises(TerminalError):
            with capture_until_primary_da():
                pass


def test_capture_terminal_response_stdin_closed() -> None:
    with patch("sys.__stdin__", None):
        with raises(TerminalError):
            with capture_terminal_response("[S]", "[E]"):
                pass


def test_capture_terminal_response_success() -> None:
    with patch("sys.__stdin__"):
        with patch("textual_image._terminal.capture_mode"):
            with patch("textual_image._terminal.read", side_effect="[S]message[E]"):
                with capture_terminal_response("[S]", "[E]") as response:
                    pass

            assert response.sequence == "[S]message[E]"


def test_capture_terminal_response_timeout() -> None:
    with patch("sys.__stdin__"):
        with patch("textual_image._terminal.capture_mode"):
            with patch("textual_image._terminal.read", side_effect=TimeoutError()):
                with raises(TimeoutError):
                    with capture_terminal_response("[S]", "[E]"):
                        pass


def test_capture_terminal_response_unexpected_response() -> None:
    with patch("sys.__stdin__"):
        with patch("textual_image._terminal.capture_mode"):
            with patch("textual_image._terminal.read", side_effect="Something unexpected"):
                with raises(TerminalError):
                    with capture_terminal_response("[S]", "[E]"):
                        pass
