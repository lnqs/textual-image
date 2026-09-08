from itertools import repeat
from unittest.mock import patch

from pytest import raises
from rich.console import Console
from rich.measure import Measurement
from syrupy.assertion import SnapshotAssertion

from tests.data import CONSOLE_OPTIONS, TEST_IMAGE
from tests.utils import load_non_seekable_bytes_io, render
from textual_image._terminal import TerminalError


def test_render(snapshot: SnapshotAssertion) -> None:
    from textual_image.renderable.tgp import Image

    renderable = Image(TEST_IMAGE, width=4)

    with patch.object(Image, "_image_id_counter", repeat(1337)):  # Encoded in diacritics, so it has to be fixed
        assert render(renderable).startswith("\x1b_Gi=1337,m=1,f=100,q=2;")


def test_overly_large() -> None:
    from textual_image.renderable.tgp import Image

    renderable = Image(TEST_IMAGE, width=2**32)
    with raises(ValueError):
        render(renderable)


def test_render_non_seekable() -> None:
    from textual_image.renderable.tgp import Image

    test_image = load_non_seekable_bytes_io(TEST_IMAGE)
    renderable = Image(test_image)
    assert test_image.read() == b""
    # encoding is not deterministic, so we don't compare the output
    render(renderable)
    render(renderable)

    test_image.close()
    render(renderable)


def test_measure() -> None:
    from textual_image.renderable.tgp import Image

    renderable = Image(TEST_IMAGE, width=4)
    assert renderable.__rich_measure__(Console(), CONSOLE_OPTIONS) == Measurement(4, 4)


def test_cleanup() -> None:
    from textual_image.renderable.tgp import Image

    renderable = Image(TEST_IMAGE, width=4)

    with patch("textual_image.renderable.tgp._send_tgp_message") as send_terminal_graphics_protocol_message:
        renderable.cleanup()
    assert not send_terminal_graphics_protocol_message.called

    with patch("textual_image.renderable.tgp._send_tgp_message") as send_terminal_graphics_protocol_message:
        render(renderable)
        renderable.cleanup()
    assert send_terminal_graphics_protocol_message.called


def test_send_tgp_message() -> None:
    from textual_image.renderable.tgp import _send_tgp_message

    with patch("sys.__stdout__", None):
        with raises(TerminalError):
            _send_tgp_message(d=42)

    with patch("sys.__stdout__") as stdout:
        _send_tgp_message(d=42)
    assert stdout.write.call_args[0][0] == "\x1b_Gd=42\x1b\\"
    assert stdout.flush.called

    with patch("textual_image._tmux.IS_TMUX", True):
        with patch("sys.__stdout__") as stdout:
            _send_tgp_message(d=42)

    assert stdout.write.call_args[0][0] == "\x1bPtmux;\x1b\x1b_Gd=42\x1b\x1b\\\x1b\\"
    assert stdout.flush.called


def test_query_terminal_support() -> None:
    from textual_image._terminal import CellSize, TerminalCapabilities, TerminalError
    from textual_image.renderable.tgp import query_terminal_support

    with patch(
        "textual_image.renderable.tgp.probe_terminal",
        return_value=TerminalCapabilities(CellSize(10, 20), sixel=False, tgp=True),
    ):
        assert query_terminal_support()

    with patch(
        "textual_image.renderable.tgp.probe_terminal",
        return_value=TerminalCapabilities(CellSize(10, 20), sixel=False, tgp=False),
    ):
        assert not query_terminal_support()

    with patch("textual_image.renderable.tgp.probe_terminal", side_effect=TerminalError()):
        assert not query_terminal_support()
