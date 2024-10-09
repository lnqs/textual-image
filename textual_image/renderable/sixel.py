"""Provides a Rich Renderable to render images as Sixels (https://en.wikipedia.org/wiki/Sixel)."""

import sys
from pathlib import Path

from PIL import Image as PILImage
from rich.console import Console, ConsoleOptions, RenderResult
from rich.control import Control
from rich.measure import Measurement
from rich.segment import ControlType, Segment

from textual_image._geometry import ImageSize
from textual_image._pixeldata import PixelData
from textual_image._sixel import image_to_sixels
from textual_image._terminal import TerminalError, capture_terminal_response, get_cell_size

# Random no-op control code to prevent Rich from messing with our data
_NULL_CONTROL = [(ControlType.CURSOR_FORWARD, 0)]


class Image:
    """Rich Renderable to render images as Sixels (https://en.wikipedia.org/wiki/Sixel)."""

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

        # Save cursor position to restore if after drawing the sixels
        yield Segment("\x1b7", control=_NULL_CONTROL)
        yield Control.move(0, -cell_height)

        scaled_image = self._image_data.scaled(pixel_width, pixel_height)
        sixel_data = image_to_sixels(scaled_image.pil_image)

        # We add a random no-op control code to prevent Rich from messing with our data
        yield Segment(sixel_data, control=_NULL_CONTROL)
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
    """Queries the terminal for Sixel support.

    This function returns if Sixels are supported.
    To do so, it sends an escape sequence to the terminal and waits for the answer.
    This is a bit flaky -- keystrokes during reading the response can lead to false answers.
    Additionally, when TGP is *not* supported and the terminal doesn't send an answer, the first character
    of stdin may get lost as this function reads it to determine if it is the response.
    Anyway, as this is improbable to happen, it should be fine. There doesn't seem to be another way to
    get this information.

    Please not this function will not work anymore once Textual is started. Textual runs a threads to read stdin
    and will grab the response.

    Returns:
        True if Sixel is supported, False if not
    """
    if not sys.__stdout__:
        return False

    try:
        with capture_terminal_response(start_marker="\x1b[?", end_marker="c", timeout=0.1) as response:
            sys.__stdout__.write("\x1b[c")
            sys.__stdout__.flush()

        sequence = response.sequence[len("\x1b[?") : -len("c")]
        return "4" in sequence.split(";")

    except (TerminalError, TimeoutError):
        pass

    return False
