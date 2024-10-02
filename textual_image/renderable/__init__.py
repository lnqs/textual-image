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

if is_tty and tgp.query_terminal_support():
    logger.debug("Terminal Graphics Protocol support detected")
    Image = TGPImage
elif is_tty and sixel.query_terminal_support():
    logger.debug("Sixel support detected")
    Image = SixelImage
elif is_tty:
    logger.debug("Connected to a terminal, using half cell rendering")
    Image = HalfcellImage
else:
    logger.debug("Not connected to a terminal, falling back to unicode")
    Image = UnicodeImage

__all__ = ["Image", "TGPImage", "SixelImage", "HalfcellImage", "UnicodeImage"]
