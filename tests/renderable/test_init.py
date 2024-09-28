from importlib import reload
from unittest.mock import patch

import textual_kitty.renderable
from textual_kitty.renderable import halfcell, sixel, tgp, unicode


def test_determining_best_renderable() -> None:
    with patch("sys.__stdout__.isatty", return_value=True):
        with patch("textual_kitty.renderable.tgp.query_terminal_support", return_value=True):
            module = reload(textual_kitty.renderable)
            assert module.Image is tgp.Image

        with patch("textual_kitty.renderable.tgp.query_terminal_support", return_value=False):
            with patch("textual_kitty.renderable.sixel.query_terminal_support", return_value=True):
                module = reload(textual_kitty.renderable)
                assert module.Image is sixel.Image

        with patch("textual_kitty.renderable.tgp.query_terminal_support", return_value=False):
            with patch("textual_kitty.renderable.sixel.query_terminal_support", return_value=False):
                module = reload(textual_kitty.renderable)
                assert module.Image is halfcell.Image

    with patch("sys.__stdout__.isatty", return_value=False):
        module = reload(textual_kitty.renderable)
        assert module.Image is unicode.Image
