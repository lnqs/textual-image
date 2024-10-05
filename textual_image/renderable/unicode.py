"""Provides a Rich Renderable to render images as grayscale unicode characters."""

from pathlib import Path
from typing import cast

from PIL import Image as PILImage
from rich.console import Console, ConsoleOptions, RenderResult
from rich.measure import Measurement
from rich.segment import Segment

from textual_image._geometry import ImageSize
from textual_image._pixeldata import PixelData
from textual_image._terminal import get_cell_size
from textual_image._utils import clamp

_CHARACTERS = [
    "█",  # FULL BLOCK
    "▓",  # DARK SHADE
    "▒",  # MEDIUM SHADE
    "░",  # LIGHT SHADE
    " ",  # SPACE
]

_CHARACTER_LOOKUP = {int(255 / len(_CHARACTERS) * i): c for i, c in enumerate(_CHARACTERS)}


def _map_pixel(pixel_value: int) -> str:
    """Maps a grayscale pixel value to a unicode character.

    Args:
        pixel_value: Pixel value in range 0-255.

    Returns:
        Unicode character resembling the pixel value.
    """
    brightness = clamp(255 - pixel_value, 1, 254)
    index = int(255 / len(_CHARACTER_LOOKUP)) * int(brightness / int(255 / len(_CHARACTER_LOOKUP)))
    return _CHARACTER_LOOKUP[index]


class Image:
    """Rich Renderable to render images as grayscale unicode characters."""

    def __init__(
        self, image: str | Path | PILImage.Image, width: int | str | None = None, height: int | str | None = None
    ) -> None:
        """Initialized the `Image`.

        Args:
            image: Path to an image file or `PIL.Image.Image` instance with the image data to render.
            width: Width specification to render the image.
                See `textual_image.geometry.ImageSize` for details about possible values.
            height: height specification to render the image.
                See `textual_image.geometry.ImageSize` for details about possible values.
        """
        self._image_data = PixelData(image, mode="grayscale")
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

        # We draw one character per pixel. Therefore we just scale to the amount of cells and are done.
        # No need to care about the scaled pixel size.
        width, height = self._render_size.get_cell_size(options.max_width, options.max_height, terminal_sizes)

        for row in self._image_data.scaled(width, height):
            yield Segment("".join(_map_pixel(cast(int, pixel)) for pixel in row) + "\n")

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
