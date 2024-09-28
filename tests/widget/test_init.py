from importlib import reload
from unittest.mock import patch

import textual_kitty.renderable
import textual_kitty.widget
from textual_kitty.renderable.sixel import Image as SixelRenderable
from textual_kitty.widget.sixel import Image as SixelImage


def test_determining_best_widget_as_sixel() -> None:
    with patch("textual_kitty.renderable.Image", SixelRenderable):
        module = reload(textual_kitty.widget)
        assert module.Image is SixelImage
