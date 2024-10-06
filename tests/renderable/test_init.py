from importlib import reload
from unittest.mock import patch


def test_determining_best_renderable() -> None:
    import textual_image.renderable
    from textual_image.renderable import halfcell, sixel, tgp, unicode

    with patch("sys.__stdout__.isatty", return_value=True):
        with patch("textual_image.renderable.tgp.query_terminal_support", return_value=True):
            module = reload(textual_image.renderable)
            assert module.Image is tgp.Image

        with patch("textual_image.renderable.tgp.query_terminal_support", return_value=False):
            with patch("textual_image.renderable.sixel.query_terminal_support", return_value=True):
                module = reload(textual_image.renderable)
                assert module.Image is sixel.Image

        with patch("textual_image.renderable.tgp.query_terminal_support", return_value=False):
            with patch("textual_image.renderable.sixel.query_terminal_support", return_value=False):
                module = reload(textual_image.renderable)
                assert module.Image is halfcell.Image

    with patch("sys.__stdout__.isatty", return_value=False):
        module = reload(textual_image.renderable)
        assert module.Image is unicode.Image
