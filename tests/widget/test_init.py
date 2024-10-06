from importlib import reload
from unittest import skipUnless
from unittest.mock import patch

from tests.data import TEXTUAL_ENABLED


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
def test_determining_best_widget_as_sixel() -> None:
    import textual_image.renderable
    import textual_image.widget
    from textual_image.renderable.sixel import Image as SixelRenderable
    from textual_image.widget.sixel import Image as SixelImage

    with patch("textual_image.renderable.Image", SixelRenderable):
        module = reload(textual_image.widget)
        assert module.Image is SixelImage
