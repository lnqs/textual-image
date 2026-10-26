from unittest.mock import patch

from rich.console import Console
from rich.measure import Measurement
from syrupy.assertion import SnapshotAssertion

from tests.data import CONSOLE_OPTIONS, TEST_IMAGE
from tests.utils import render


def test_build_iterm2_sequence() -> None:
    from textual_image.renderable.iterm2 import _build_iterm2_sequence

    seq = _build_iterm2_sequence("abc123", 100, 200)
    assert seq.startswith("\x1b]1337;File=")
    assert "width=100px" in seq
    assert "height=200px" in seq
    assert "inline=1" in seq
    assert "preserveAspectRatio=0" in seq
    assert ":abc123\x07" in seq


def test_render(snapshot: SnapshotAssertion) -> None:
    from textual_image.renderable.iterm2 import Image

    renderable = Image(TEST_IMAGE, width=4)
    assert render(renderable) == snapshot


def test_measure() -> None:
    from textual_image.renderable.iterm2 import Image

    renderable = Image(TEST_IMAGE, width=4)
    assert renderable.__rich_measure__(Console(), CONSOLE_OPTIONS) == Measurement(4, 4)


def test_cleanup() -> None:
    from textual_image.renderable.iterm2 import Image

    Image(TEST_IMAGE, width=4).cleanup()


def test_query_terminal_support_no_stdout() -> None:
    from textual_image.renderable.iterm2 import query_terminal_support

    with patch("sys.__stdout__", None):
        assert not query_terminal_support()


def test_query_terminal_support_iterm2_env() -> None:
    from textual_image.renderable.iterm2 import query_terminal_support

    with patch("sys.__stdout__"), patch.dict("os.environ", {"TERM_PROGRAM": "iTerm2"}):
        assert query_terminal_support()


def test_query_terminal_support_wezterm_env() -> None:
    from textual_image.renderable.iterm2 import query_terminal_support

    with patch("sys.__stdout__"), patch.dict("os.environ", {"TERM_PROGRAM": "WezTerm"}):
        assert query_terminal_support()


def test_query_terminal_support_unknown_env() -> None:
    from textual_image.renderable.iterm2 import query_terminal_support

    with patch("sys.__stdout__"), patch.dict("os.environ", {"TERM_PROGRAM": "xterm-256color"}):
        assert not query_terminal_support()
