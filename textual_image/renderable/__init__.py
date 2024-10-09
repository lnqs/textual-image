"""Rich renderables to display images in terminal."""

import logging
import sys
from typing import Type

from textual_image.renderable import sixel, tgp
from textual_image.renderable.halfcell import Image as HalfcellImage
from textual_image.renderable.sixel import Image as SixelImage
from textual_image.renderable.tgp import Image as TGPImage
from textual_image.renderable.unicode import Image as UnicodeImage

logger = logging.getLogger(__name__)

is_tty = sys.__stdout__ and sys.__stdout__.isatty()

Image: Type[TGPImage | SixelImage | HalfcellImage | UnicodeImage]

# TGP should be on top, as it performs way better than Sixel.
# However, the only terminal with TGP unicode diacritic support I know of is Kitty.
# Konsole and wezterm report TGP support, but don't work with our placeholder implementation, but do with Sixel.
# As Kitty does *not* support Sixel, this order should be best in terms of compatibility.
if is_tty and sixel.query_terminal_support():
    logger.debug("Sixel support detected")
    Image = SixelImage
elif is_tty and tgp.query_terminal_support():
    logger.debug("Terminal Graphics Protocol support detected")
    Image = TGPImage
elif is_tty:
    logger.debug("Connected to a terminal, using half cell rendering")
    Image = HalfcellImage
else:
    logger.debug("Not connected to a terminal, falling back to unicode")
    Image = UnicodeImage

__all__ = ["Image", "TGPImage", "SixelImage", "HalfcellImage", "UnicodeImage"]
