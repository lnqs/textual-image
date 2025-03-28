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
    from textual_image.renderable.sixel import Image

    renderable = Image(TEST_IMAGE, width=4)
    assert render(renderable) == snapshot


def test_render_non_seekable() -> None:
    from textual_image.renderable.sixel import Image

    test_image = load_non_seekable_bytes_io(TEST_IMAGE)
    renderable = Image(test_image)
    assert test_image.read() == b""
    assert render(renderable) == render(renderable)

    test_image.close()
    assert render(renderable) == render(renderable)


def test_measure() -> None:
    from textual_image.renderable.sixel import Image

    renderable = Image(TEST_IMAGE, width=4)
    assert renderable.__rich_measure__(Console(), CONSOLE_OPTIONS) == Measurement(4, 4)


def test_cleanup() -> None:
    from textual_image.renderable.sixel import Image

    # cleanup() is a no-op. Let's call it anyway.
    Image(TEST_IMAGE, width=4).cleanup()


def test_query_terminal_support() -> None:
    from textual_image.renderable.sixel import query_terminal_support

    @contextmanager
    def response_success(start_marker: str, end_marker: str, timeout: float | None = None) -> Iterator[SimpleNamespace]:
        yield SimpleNamespace(sequence="\x1b[?1;2;3;4c")

    @contextmanager
    def response_failure(start_marker: str, end_marker: str, timeout: float | None = None) -> Iterator[SimpleNamespace]:
        yield SimpleNamespace(sequence="\x1b[?1;2;3;c")

    @contextmanager
    def response_exception(
        start_marker: str, end_marker: str, timeout: float | None = None
    ) -> Iterator[SimpleNamespace]:
        raise TimeoutError()

    with patch("sys.__stdout__", None):
        assert not query_terminal_support()

    with patch("textual_image.renderable.sixel.capture_terminal_response", response_success):
        with patch("sys.__stdout__"):
            assert query_terminal_support()

    with patch("textual_image.renderable.sixel.capture_terminal_response", response_failure):
        with patch("sys.__stdout__"):
            assert not query_terminal_support()

    with patch("textual_image.renderable.sixel.capture_terminal_response", response_exception):
        with patch("sys.__stdout__"):
            assert not query_terminal_support()
