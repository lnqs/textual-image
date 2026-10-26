"""Provides a Rich Renderable to render images via the iTerm2 Inline Images Protocol (https://iterm2.com/documentation-images.html)."""

import logging
import os
import sys
from typing import IO

from PIL import Image as PILImage
from rich.console import Console, ConsoleOptions, RenderResult
from rich.control import Control
from rich.measure import Measurement
from rich.segment import ControlType, Segment

from textual_image._geometry import ImageSize
from textual_image._pixeldata import PixelData
from textual_image._terminal import get_cell_size
from textual_image._utils import StrOrBytesPath

logger = logging.getLogger(__name__)

# Random no-op control code to prevent Rich from messing with our data
_NULL_CONTROL = [(ControlType.CURSOR_FORWARD, 0)]


def _build_iterm2_sequence(image_data_b64: str, pixel_width: int, pixel_height: int) -> str:
    """Build an iTerm2 inline image escape sequence.

    Args:
        image_data_b64: Base64-encoded image data (PNG).
        pixel_width: Width to render in pixels.
        pixel_height: Height to render in pixels.

    Returns:
        The complete escape sequence string.
    """
    return (
        f"\x1b]1337;File="
        f"inline=1;"
        f"width={pixel_width}px;"
        f"height={pixel_height}px;"
        f"preserveAspectRatio=0"
        f":{image_data_b64}\x07"
    )


class Image:
    """Rich Renderable to render images via the iTerm2 Inline Images Protocol (<https://iterm2.com/documentation-images.html>)."""

    def __init__(
        self,
        image: StrOrBytesPath | IO[bytes] | PILImage.Image,
        width: int | str | None = None,
        height: int | str | None = None,
    ) -> None:
        """Initialized the `Image`.

        Args:
            image: Path to an image file, a byte stream containing image data, or `PIL.Image.Image` instance with the
                   image data to render.
            width: Width specification to render the image.
                See `textual_image.geometry.ImageSize` for details about possible values.
            height: height specification to render the image.
                See `textual_image.geometry.ImageSize` for details about possible values.
        """
        self._image_data = PixelData(image)
        self._render_size = ImageSize(self._image_data.width, self._image_data.height, width, height)

    def cleanup(self) -> None:
        """No-op."""
        pass

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        """Called by Rich to render the `Image`.

        Args:
            console: The `Console` instance to render to.
            options: Options for rendering, i.e. available size information.

        Returns:
            `Segment`s to display.
        """
        terminal_sizes = get_cell_size()

        cell_width, cell_height = self._render_size.get_cell_size(options.max_width, options.max_height, terminal_sizes)
        pixel_width, pixel_height = self._render_size.get_pixel_size(
            options.max_width, options.max_height, terminal_sizes
        )

        # Add a text placeholder for the image that'll be overwritten with the actual image.
        # This way rich realizes how much space the renderable uses.
        for _ in range(cell_height):
            yield Segment(" " * cell_width + "\n")

        # Save cursor position to restore after drawing the image
        yield Segment("\x1b7", control=_NULL_CONTROL)
        yield Control.move(0, -cell_height)

        image_data_b64 = self._image_data.scaled(pixel_width, pixel_height).to_base64()
        sequence = _build_iterm2_sequence(image_data_b64, pixel_width, pixel_height)

        # We add a random no-op control code to prevent Rich from messing with our data
        yield Segment(sequence, control=_NULL_CONTROL)
        yield Segment("\x1b8", control=_NULL_CONTROL)

    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
        """Called by Rich to get the render width without actually rendering the object.

        Args:
            console: The `Console` instance to render to.
            options: Options for rendering, i.e. available size information.

        Returns:
            A `Measurement` containing minimum and maximum widths required to render the object
        """
        terminal_sizes = get_cell_size()
        width, _ = self._render_size.get_cell_size(options.max_width, options.max_height, terminal_sizes)
        return Measurement(width, width)


def query_terminal_support() -> bool:
    """Queries the terminal for iTerm2 Inline Images Protocol support.

    Returns:
        True if the iTerm2 Inline Images Protocol is supported, False if not
    """
    if not sys.__stdout__:
        return False

    # Check TERM_PROGRAM environment variable for quick detection
    if os.environ.get("TERM_PROGRAM") in ("iTerm2", "WezTerm"):
        return True

    # need some help with feature reporting protocol
    # iterm2's documentation says https://iterm2.com/feature-reporting but it
    # doesnt work on wezterm, and i dont own a mac, so, help i guess?

    return False
