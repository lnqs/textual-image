from contextlib import contextmanager
from types import SimpleNamespace
from typing import Iterator
from unittest.mock import patch

from rich.console import Console
from rich.measure import Measurement
from syrupy.assertion import SnapshotAssertion

from tests.data import CONSOLE_OPTIONS, TEST_IMAGE
from tests.utils import load_non_seekable_bytes_io, render


def test_render(snapshot: SnapshotAssertion) -> None:
    from textual_image.renderable.iterm2 import Image

    renderable = Image(TEST_IMAGE, width=4)
    assert render(renderable) == snapshot


def test_render_non_seekable() -> None:
    from textual_image.renderable.iterm2 import Image

    test_image = load_non_seekable_bytes_io(TEST_IMAGE)
    renderable = Image(test_image)
    assert test_image.read() == b""
    assert render(renderable) == render(renderable)

    test_image.close()
    assert render(renderable) == render(renderable)


def test_measure() -> None:
    from textual_image.renderable.iterm2 import Image

    renderable = Image(TEST_IMAGE, width=4)
    assert renderable.__rich_measure__(Console(), CONSOLE_OPTIONS) == Measurement(4, 4)


def test_cleanup() -> None:
    from textual_image.renderable.iterm2 import Image

    # cleanup() is a no-op. Let's call it anyway.
    Image(TEST_IMAGE, width=4).cleanup()


def test_build_iterm2_sequence() -> None:
    from textual_image.renderable.iterm2 import _build_iterm2_sequence

    result = _build_iterm2_sequence("AAAA", 100, 200)
    assert result == "\x1b]1337;File=inline=1;width=100px;height=200px;preserveAspectRatio=0:AAAA\x07"


def test_query_terminal_support_via_env() -> None:
    from textual_image.renderable.iterm2 import query_terminal_support

    with patch.dict("os.environ", {"TERM_PROGRAM": "iTerm2"}):
        with patch("sys.__stdout__"):
            assert query_terminal_support()

    with patch.dict("os.environ", {"TERM_PROGRAM": "other"}, clear=True):
        with patch("sys.__stdout__"):
            # Will fall through to capability check which will fail
            with patch(
                "textual_image.renderable.iterm2.capture_terminal_response",
                side_effect=TimeoutError(),
            ):
                assert not query_terminal_support()


def test_query_terminal_support_via_capabilities() -> None:
    from textual_image.renderable.iterm2 import (
        _OSC_1337_END,
        _OSC_1337_START,
        query_terminal_support,
    )

    @contextmanager
    def response_with_file(
        start_marker: str, end_marker: str, timeout: float | None = None
    ) -> Iterator[SimpleNamespace]:
        yield SimpleNamespace(sequence=f"{_OSC_1337_START}Capabilities=T3CwLrMSc7UBFGsSyHNoSxFP{_OSC_1337_END}")

    @contextmanager
    def response_without_file(
        start_marker: str, end_marker: str, timeout: float | None = None
    ) -> Iterator[SimpleNamespace]:
        yield SimpleNamespace(sequence=f"{_OSC_1337_START}Capabilities=T3CwLrMSc7UBGsSyHNoSxP{_OSC_1337_END}")

    @contextmanager
    def response_exception(
        start_marker: str, end_marker: str, timeout: float | None = None
    ) -> Iterator[SimpleNamespace]:
        raise TimeoutError()

    with patch.dict("os.environ", {}, clear=True):
        with patch("textual_image.renderable.iterm2.capture_terminal_response", response_with_file):
            with patch("sys.__stdout__"):
                assert query_terminal_support()

        with patch("textual_image.renderable.iterm2.capture_terminal_response", response_without_file):
            with patch("sys.__stdout__"):
                assert not query_terminal_support()

        with patch("textual_image.renderable.iterm2.capture_terminal_response", response_exception):
            with patch("sys.__stdout__"):
                assert not query_terminal_support()


def test_query_terminal_support_no_stdout() -> None:
    from textual_image.renderable.iterm2 import query_terminal_support

    with patch("sys.__stdout__", None):
        assert not query_terminal_support()
