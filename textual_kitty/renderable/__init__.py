"""rich `Renderable`s to display images in terminal."""

import logging
import sys
from typing import Type

from textual_kitty.renderable import tgp
from textual_kitty.renderable.fallback import colored, grayscale

logger = logging.getLogger(__name__)

Image: Type[tgp.Image | colored.Image | grayscale.Image]

is_tty = sys.__stdout__ and sys.__stdout__.isatty()

if is_tty and tgp.query_terminal_support():
    logger.debug("Terminal Graphics Protocol support detected")
    Image = tgp.Image
elif is_tty:
    logger.debug("No Terminal Graphics Protocol support detected, falling back to colored unicode")
    Image = colored.Image
else:
    logger.debug("Not connected to a terminal, falling back to grayscale unicode")
    Image = grayscale.Image
