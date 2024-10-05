"""Provides a Rich Renderable to render images as colored half cells."""

from pathlib import Path
from typing import Tuple

from PIL import Image as PILImage
from rich.color import Color
from rich.color_triplet import ColorTriplet
from rich.console import Console, ConsoleOptions, RenderResult
from rich.measure import Measurement
from rich.segment import Segment
from rich.style import Style

from textual_image._geometry import ImageSize
from textual_image._pixeldata import PixelData
from textual_image._terminal import get_cell_size
from textual_image._utils import grouped


def _map_pixel(pixel_value: Tuple[int, int, int]) -> Color:
    """Maps a pixel value to a colored halfcells.

    Args:
        pixel_value: Pixel value in three integers in range 0-255 for the R, G and B channels.

    Returns:
        Color resembling the pixel value.
    """
    return Color.from_triplet(ColorTriplet(*pixel_value))


class Image:
    """Rich Renderable to render images as colored half cells."""

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
        self._image_data = PixelData(image, mode="rgb")
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

        # We draw two characters per pixel. Therefore we just scale to the amount of cells,
        # take the height times two and are done. No need to care about the scaled pixel size.
        width, height = self._render_size.get_cell_size(options.max_width, options.max_height, terminal_sizes)
        height *= 2

        for upper_row, lower_row in grouped(self._image_data.scaled(width, height), 2):
            for upper_pixel, lower_pixel in zip(upper_row, lower_row):
                yield Segment("▀", style=Style(color=_map_pixel(upper_pixel), bgcolor=_map_pixel(lower_pixel)))  # type: ignore
            yield Segment("\n")

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
