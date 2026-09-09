from itertools import repeat
import re
from unittest.mock import patch

from rich.console import Console
from rich.measure import Measurement

from tests.data import CONSOLE_OPTIONS, TEST_IMAGE
from tests.utils import load_non_seekable_bytes_io, render


def test_render() -> None:
    from textual_image.renderable.kitty import Image

    renderable = Image(TEST_IMAGE, width=4)

    with patch.object(Image, "_image_id_counter", repeat(1337)):
        output = render(renderable)

    assert "\x1b7" in output
    assert re.search(r"\x1b_Ga=T,i=1337,c=4,r=\d+,C=1,f=100,m=[01],q=2;", output)
    assert output.endswith("\x1b8")


def test_render_non_seekable() -> None:
    from textual_image.renderable.kitty import Image

    test_image = load_non_seekable_bytes_io(TEST_IMAGE)
    renderable = Image(test_image)
    assert test_image.read() == b""

    first = render(renderable)
    second = render(renderable)

    assert "\x1b7" in first
    assert "\x1b7" in second

    test_image.close()
    assert "\x1b7" in render(renderable)


def test_measure() -> None:
    from textual_image.renderable.kitty import Image

    renderable = Image(TEST_IMAGE, width=4)
    assert renderable.__rich_measure__(Console(), CONSOLE_OPTIONS) == Measurement(4, 4)


def test_cleanup() -> None:
    from textual_image.renderable.kitty import Image

    renderable = Image(TEST_IMAGE, width=4)

    with patch("textual_image.renderable.kitty._send_tgp_message") as send_tgp_message:
        renderable.cleanup()

    assert not send_tgp_message.called

    with patch.object(Image, "_image_id_counter", repeat(1337)):
        render(renderable)

    with patch("textual_image.renderable.kitty._send_tgp_message") as send_tgp_message:
        renderable.cleanup()

    assert send_tgp_message.call_args.kwargs == {"a": "d", "d": "I", "i": 1337, "q": 2}


def test_build_tgp_message() -> None:
    from textual_image.renderable.kitty import _build_tgp_message

    assert _build_tgp_message(a="T", i=42, payload="AAAA") == "\x1b_Ga=T,i=42;AAAA\x1b\\"


def test_query_terminal_support() -> None:
    from textual_image.renderable.kitty import query_terminal_support

    with patch("textual_image.renderable.kitty.query_tgp_terminal_support", return_value=True):
        assert query_terminal_support()

    with patch("textual_image.renderable.kitty.query_tgp_terminal_support", return_value=False):
        assert not query_terminal_support()
