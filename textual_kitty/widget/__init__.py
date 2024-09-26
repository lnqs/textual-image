"""Textual `Widget` to display images in terminal."""

from textual_kitty.renderable import Image as AutoRenderable
from textual_kitty.renderable.halfcell import Image as HalfcellRenderable
from textual_kitty.renderable.tgp import Image as TGPRenderable
from textual_kitty.renderable.unicode import Image as UnicodeRenderable
from textual_kitty.widget._base import Image as BaseImage


class Image(BaseImage, Renderable=AutoRenderable):
    """Textual `Widget` to render images in the terminal using the best available method."""

    pass


class TGPImage(BaseImage, Renderable=TGPRenderable):
    """Textual `Widget` to render images in the terminal using the Terminal Graphics Protocol (<https://sw.kovidgoyal.net/kitty/graphics-protocol/>)."""

    pass


class HalfcellImage(BaseImage, Renderable=HalfcellRenderable):
    """Textual `Widget` to render images in the terminal using colored half cells."""

    pass


class UnicodeImage(BaseImage, Renderable=UnicodeRenderable):
    """Textual `Widget` to render images in the terminal using unicode characters."""

    pass
