import re
from unittest.mock import patch

from rich.console import Console
from rich.measure import Measurement

from tests.data import CONSOLE_OPTIONS, TEST_IMAGE
from tests.utils import load_non_seekable_bytes_io, render


def test_build_iterm2_sequence() -> None:
    from textual_image.renderable.iterm2 import _build_iterm2_sequence

    seq = _build_iterm2_sequence("abc123", pixel_width=100, pixel_height=50)

    assert seq.startswith("\x1b]1337;File=")
    assert seq.endswith("\x07")
    assert "inline=1" in seq
    assert "width=100px" in seq
    assert "height=50px" in seq
    assert "preserveAspectRatio=0" in seq
    assert ":abc123" in seq


def test_render() -> None:
    from textual_image.renderable.iterm2 import Image

    renderable = Image(TEST_IMAGE, width=4)
    output = render(renderable)

    assert "\x1b]1337;File=" in output
    assert "inline=1" in output
    assert re.search(r"width=\d+px", output)
    assert re.search(r"height=\d+px", output)
    assert "\x07" in output
    assert "\x1b8" in output


def test_render_non_seekable() -> None:
    from textual_image.renderable.iterm2 import Image

    test_image = load_non_seekable_bytes_io(TEST_IMAGE)
    renderable = Image(test_image)
    assert test_image.read() == b""

    first = render(renderable)
    second = render(renderable)
    assert first == second

    test_image.close()
    assert render(renderable) == first


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


def test_query_terminal_support_iterm2() -> None:
    from textual_image.renderable.iterm2 import query_terminal_support

    with patch("sys.__stdout__"), patch.dict("os.environ", {"TERM_PROGRAM": "iTerm2"}):
        assert query_terminal_support()


def test_query_terminal_support_wezterm() -> None:
    from textual_image.renderable.iterm2 import query_terminal_support

    with patch("sys.__stdout__"), patch.dict("os.environ", {"TERM_PROGRAM": "WezTerm"}):
        assert query_terminal_support()


def test_query_terminal_support_unknown_terminal() -> None:
    from textual_image.renderable.iterm2 import query_terminal_support

    with patch("sys.__stdout__"), patch.dict("os.environ", {"TERM_PROGRAM": "xterm-256color"}):
        assert not query_terminal_support()


def test_query_terminal_support_no_term_program() -> None:
    import os

    from textual_image.renderable.iterm2 import query_terminal_support

    env = {k: v for k, v in os.environ.items() if k != "TERM_PROGRAM"}
    with patch("sys.__stdout__"), patch.dict("os.environ", env, clear=True):
        assert not query_terminal_support()
