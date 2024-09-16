from contextlib import contextmanager
from types import SimpleNamespace
from typing import Iterator
from unittest.mock import patch

from pytest import raises
from syrupy.assertion import SnapshotAssertion

from tests.data import SIZE_TEN, SIZE_ZERO, TERM_SIZE, TEST_IMAGE
from tests.util import render
from textual_kitty.renderable.tgp import (
    Image,
    _capture_tgp_response,
    _send_tgp_message,
    query_terminal_support,
)
from textual_kitty.terminal import TerminalError


def test_cleanup() -> None:
    renderable = Image(TEST_IMAGE)

    with patch("textual_kitty.renderable.tgp._send_tgp_message") as send_terminal_graphics_protocol_message:
        renderable.cleanup()
    assert not send_terminal_graphics_protocol_message.called

    with patch("textual_kitty.renderable.tgp._send_tgp_message") as send_terminal_graphics_protocol_message:
        render(renderable)
        renderable.cleanup()
    assert send_terminal_graphics_protocol_message.called


def test_prepare() -> None:
    renderable = Image(TEST_IMAGE)

    assert not renderable.is_prepared(SIZE_TEN, TERM_SIZE)

    with patch("textual_kitty.renderable.tgp._send_tgp_message") as send_terminal_graphics_protocol_message:
        renderable.prepare(SIZE_TEN, TERM_SIZE)

    assert send_terminal_graphics_protocol_message.called
    assert renderable.is_prepared(SIZE_TEN, TERM_SIZE)
    assert not renderable.is_prepared(SIZE_ZERO, TERM_SIZE)

    with patch("textual_kitty.renderable.tgp._send_tgp_message") as send_terminal_graphics_protocol_message:
        renderable.cleanup()

    assert send_terminal_graphics_protocol_message.called
    assert not renderable.is_prepared(SIZE_TEN, TERM_SIZE)


async def test_prepare_async() -> None:
    renderable = Image(TEST_IMAGE)

    assert not renderable.is_prepared(SIZE_TEN, TERM_SIZE)

    with patch("textual_kitty.renderable.tgp._send_tgp_message") as send_terminal_graphics_protocol_message:
        await renderable.prepare_async(SIZE_TEN, TERM_SIZE)

    assert send_terminal_graphics_protocol_message.called
    assert renderable.is_prepared(SIZE_TEN, TERM_SIZE)
    assert not renderable.is_prepared(SIZE_ZERO, TERM_SIZE)

    with patch("textual_kitty.renderable.tgp._send_tgp_message") as send_terminal_graphics_protocol_message:
        renderable.cleanup()

    assert send_terminal_graphics_protocol_message.called
    assert not renderable.is_prepared(SIZE_TEN, TERM_SIZE)


def test_render(snapshot: SnapshotAssertion) -> None:
    renderable = Image(TEST_IMAGE, width=4)
    renderable.terminal_image_id = 1337  # Encoded in diacritics, so it has to be fixed

    assert list(renderable._render()) == []

    with patch("textual_kitty.renderable.tgp._send_tgp_message"):
        assert render(renderable) == snapshot


def test_send_tgp_message() -> None:
    with patch("sys.__stdout__", None):
        with raises(TerminalError):
            _send_tgp_message(d=42)

    with patch("sys.__stdout__") as stdout:
        _send_tgp_message(d=42)
    assert stdout.write.call_args[0][0] == "\x1b_Gd=42\x1b\\"
    assert stdout.flush.called


def test_capture_tgp_response() -> None:
    with patch("sys.__stdin__", None):
        with raises(TerminalError):
            with _capture_tgp_response():
                pass

    with patch("sys.__stdin__") as stdin, patch("termios.tcgetattr"), patch("termios.tcsetattr"), patch(
        "tty.setcbreak"
    ), patch("textual_kitty.renderable.tgp.select") as select, patch("os.read") as read:
        stdin.buffer.fileno.return_value = 42
        select.return_value = [[42], [], []]
        read.side_effect = [c.to_bytes() for c in b"\x1b_Gd=1;OK\x1b\\"]

        with _capture_tgp_response() as response:
            pass

        assert response.status == "OK"
        assert response.params == {"d": "1"}

    with patch("sys.__stdin__") as stdin, patch("termios.tcgetattr"), patch("termios.tcsetattr"), patch(
        "tty.setcbreak"
    ), patch("textual_kitty.renderable.tgp.select") as select:
        stdin.buffer.fileno.return_value = 42
        select.return_value = [[], [], []]

        with raises(TimeoutError):
            with _capture_tgp_response():
                pass

    with patch("sys.__stdin__") as stdin, patch("termios.tcgetattr"), patch("termios.tcsetattr"), patch(
        "tty.setcbreak"
    ), patch("textual_kitty.renderable.tgp.select") as select, patch("os.read") as read:
        stdin.buffer.fileno.return_value = 42
        select.return_value = [[42], [], []]
        read.side_effect = [c.to_bytes() for c in b"not a tgp message"]

        with raises(TerminalError):
            with _capture_tgp_response() as response:
                pass


def test_query_terminal_support() -> None:
    @contextmanager
    def capture_tgp_response_success(timeout: float | None = None) -> Iterator[SimpleNamespace]:
        yield SimpleNamespace(status="OK", params={"d": "1"})

    @contextmanager
    def capture_tgp_response_failure(timeout: float | None = None) -> Iterator[SimpleNamespace]:
        yield SimpleNamespace(status="FAIL", params={})

    @contextmanager
    def capture_tgp_response_exception(timeout: float | None = None) -> Iterator[SimpleNamespace]:
        raise TimeoutError()

    with patch("textual_kitty.renderable.tgp._capture_tgp_response", capture_tgp_response_success):
        with patch("textual_kitty.renderable.tgp._send_tgp_message"):
            assert query_terminal_support()

    with patch("textual_kitty.renderable.tgp._capture_tgp_response", capture_tgp_response_failure):
        with patch("textual_kitty.renderable.tgp._send_tgp_message"):
            assert not query_terminal_support()

    with patch("textual_kitty.renderable.tgp._capture_tgp_response", capture_tgp_response_exception):
        with patch("textual_kitty.renderable.tgp._send_tgp_message"):
            assert not query_terminal_support()
