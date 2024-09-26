"""Rich renderables to display images in terminal."""

import logging
import sys
from typing import Type

from textual_kitty.renderable import tgp
from textual_kitty.renderable.halfcell import Image as HalfcellImage
from textual_kitty.renderable.tgp import Image as TGPImage
from textual_kitty.renderable.unicode import Image as UnicodeImage

logger = logging.getLogger(__name__)

is_tty = sys.__stdout__ and sys.__stdout__.isatty()

Image: Type[TGPImage | HalfcellImage | UnicodeImage]

if is_tty and tgp.query_terminal_support():
    logger.debug("Terminal Graphics Protocol support detected")
    Image = TGPImage
elif is_tty:
    logger.debug("Connected to a terminal, using half cell rendering")
    Image = HalfcellImage
else:
    logger.debug("Not connected to a terminal, falling back to unicode")
    Image = UnicodeImage

__all__ = ["Image", "TGPImage", "HalfcellImage", "UnicodeImage"]
