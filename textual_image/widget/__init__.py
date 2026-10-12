"""Textual `Widget` to display images in terminal."""

from typing import Type

from textual_image._terminal import get_cell_size
from textual_image.renderable import Image as AutoRenderable
from textual_image.renderable.halfcell import Image as HalfcellRenderable
from textual_image.renderable.kitty import Image as KittyRenderable
from textual_image.renderable.sixel import Image as SixelRenderable
from textual_image.renderable.sixel import SixelOptions
from textual_image.renderable.tgp import Image as TGPRenderable
from textual_image.renderable.unicode import Image as UnicodeRenderable
from textual_image.widget._base import Image as BaseImage
from textual_image.widget.kitty import Image as KittyImage
from textual_image.widget.sixel import Image as SixelImage

# Run `get_cell_size()` once to fill the cache,
# as querying the terminal isn't possible anymore once Textual is started.
get_cell_size()


class AutoImage(BaseImage, Renderable=AutoRenderable):
    """Textual `Widget` to render images in the terminal using the best available method."""

    pass


# This is bit annoying, but as all renderables but the Sixel one can just be thrown in the base class, while
# we need a dedicated one for Sixel, we have to do this `if`.
if AutoRenderable is SixelRenderable:
    Image: Type[AutoImage | SixelImage] = SixelImage
else:
    Image = AutoImage


class TGPImage(BaseImage, Renderable=TGPRenderable):
    """Textual `Widget` to render images in the terminal using the Terminal Graphics Protocol (<https://sw.kovidgoyal.net/kitty/graphics-protocol/>)."""

    pass


class HalfcellImage(BaseImage, Renderable=HalfcellRenderable):
    """Textual `Widget` to render images in the terminal using colored half cells."""

    pass


class UnicodeImage(BaseImage, Renderable=UnicodeRenderable):
    """Textual `Widget` to render images in the terminal using unicode characters."""

    pass


# When auto-detection picks a protocol that requires Textual-specific rendering (crop/viewport context),
# use the widget version instead of the renderable directly.
if AutoRenderable is TGPRenderable:
    Image: Type[AutoImage | TGPImage | KittyImage | ITerm2Image | SixelImage] = TGPImage
elif AutoRenderable is KittyRenderable:
    Image = KittyImage
elif AutoRenderable is ITerm2Renderable:
    Image = ITerm2Image
elif AutoRenderable is SixelRenderable:
    Image = SixelImage
else:
    Image = AutoImage


__all__ = [
    "Image",
    "TGPImage",
    "KittyImage",
    "SixelImage",
    "SixelOptions",
    "HalfcellImage",
    "UnicodeImage",
]
