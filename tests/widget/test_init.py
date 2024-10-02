from importlib import reload
from unittest import skipUnless
from unittest.mock import patch

from tests.data import TEXTUAL_ENABLED
from textual_kitty.renderable.sixel import Image as SixelRenderable


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
def test_determining_best_widget_as_sixel() -> None:
    import textual_kitty.renderable
    import textual_kitty.widget
    from textual_kitty.widget.sixel import Image as SixelImage

    with patch("textual_kitty.renderable.Image", SixelRenderable):
        module = reload(textual_kitty.widget)
        assert module.Image is SixelImage
