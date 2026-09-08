"""Provides a Rich Renderable to render images as Sixels (https://en.wikipedia.org/wiki/Sixel)."""

from typing import IO, ClassVar

from PIL import Image as PILImage
from rich.console import Console, ConsoleOptions, RenderResult
from rich.control import Control
from rich.measure import Measurement
from rich.segment import ControlType, Segment

from textual_image._geometry import ImageSize
from textual_image._pixeldata import PixelData
from textual_image._sixel import SixelOptions, image_to_sixels
from textual_image._terminal import TerminalError, get_cell_size, probe_terminal
from textual_image._utils import StrOrBytesPath

# Random no-op control code to prevent Rich from messing with our data
_NULL_CONTROL = [(ControlType.CURSOR_FORWARD, 0)]


class Image:
    """Rich Renderable to render images as Sixels (https://en.wikipedia.org/wiki/Sixel)."""

    DEFAULT_OPTIONS: ClassVar[SixelOptions | None] = None
    """Default ``SixelOptions`` used when no ``sixel_options`` is passed to ``__init__``.

    ``None`` defers to ``image_to_sixels``' own default.  Subclasses can
    override this to change the project-wide default without having to pass
    ``sixel_options`` at every call site.
    """

    def __init__(
        self,
        image: StrOrBytesPath | IO[bytes] | PILImage.Image,
        width: int | str | None = None,
        height: int | str | None = None,
        sixel_options: SixelOptions | None = None,
    ) -> None:
        """Initialized the `Image`.

        Args:
            image: Path to an image file, a byte stream containing image data, or `PIL.Image.Image` instance with the
                   image data to render.
            width: Width specification to render the image.
                See `textual_image.geometry.ImageSize` for details about possible values.
            height: height specification to render the image.
                See `textual_image.geometry.ImageSize` for details about possible values.
            sixel_options: Sixel encoding options.  When ``None``, falls back to
                ``self.DEFAULT_OPTIONS``.
        """
        self._image_data = PixelData(image)
        self._render_size = ImageSize(self._image_data.width, self._image_data.height, width, height)
        self._sixel_options = sixel_options if sixel_options is not None else self.DEFAULT_OPTIONS

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
        sixel_data = image_to_sixels(scaled_image.pil_image, self._sixel_options)

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

    Uses the shared terminal capability probe (batched with TGP and cell-size queries).
    Please note this function will not work anymore once Textual is started. Textual runs a thread to read stdin
    and will grab the response.

    Returns:
        True if Sixel is supported, False if not
    """
    try:
        return probe_terminal().sixel
    except TerminalError:
        return False


__all__ = ["Image", "SixelOptions", "query_terminal_support"]
