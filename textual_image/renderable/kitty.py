"""Provides a Rich Renderable implementing basic kitty graphics protocol placement."""

from itertools import count
from random import randint
from typing import IO

from PIL import Image as PILImage
from rich.console import Console, ConsoleOptions, RenderResult
from rich.control import Control
from rich.measure import Measurement
from rich.segment import ControlType, Segment

from textual_image._geometry import ImageSize
from textual_image._pixeldata import PixelData
from textual_image._terminal import TerminalError, get_cell_size
from textual_image._utils import StrOrBytesPath
from textual_image.renderable.tgp import _send_tgp_message, query_terminal_support as query_tgp_terminal_support

# Random no-op control code to prevent Rich from messing with our data
_NULL_CONTROL = [(ControlType.CURSOR_FORWARD, 0)]

_TGP_MESSAGE_START = "\x1b_G"
_TGP_MESSAGE_END = "\x1b\\"


def _build_tgp_message(*, payload: str | None = None, **kwargs: int | str | None) -> str:
    return "".join(
        [
            _TGP_MESSAGE_START,
            ",".join(f"{k}={v}" for k, v in kwargs.items() if v is not None),
            f";{payload}" if payload else "",
            _TGP_MESSAGE_END,
        ]
    )


class Image:
    """Rich Renderable implementing basic kitty graphics protocol image placement."""

    _image_id_counter = count(randint(1, 2**32))

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
            height: Height specification to render the image.
                See `textual_image.geometry.ImageSize` for details about possible values.
        """
        self._image_data = PixelData(image)
        self._render_size = ImageSize(self._image_data.width, self._image_data.height, width, height)
        self._terminal_image_id: int | None = None

    def cleanup(self) -> None:
        """Free image data from terminal.

        Clears image data from terminal. If data wasn't sent yet or is already freed, this method is a no-op.
        """
        if self._terminal_image_id is None:
            return

        try:
            _send_tgp_message(a="d", d="I", i=self._terminal_image_id, q=2)
        except TerminalError:
            pass
        finally:
            self._terminal_image_id = None

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

        if self._terminal_image_id is None:
            self._terminal_image_id = next(self._image_id_counter)

        # Add a text placeholder for the image that'll be overwritten with the actual image.
        # This way rich realizes how much space the renderable uses.
        for _ in range(cell_height):
            yield Segment(" " * cell_width + "\n")

        # Save cursor position to restore after drawing the image.
        yield Segment("\x1b7", control=_NULL_CONTROL)
        yield Control.move(0, -cell_height)

        scaled_image = self._image_data.scaled(pixel_width, pixel_height)
        control_data = self._image_to_control_data(scaled_image.to_base64(), cell_width, cell_height)

        # We add a random no-op control code to prevent Rich from messing with our data
        yield Segment(control_data, control=_NULL_CONTROL)
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

    def _image_to_control_data(self, image_data_b64: str, cell_width: int, cell_height: int) -> str:
        assert self._terminal_image_id is not None

        chunks: list[str] = []
        while image_data_b64:
            chunk, image_data_b64 = image_data_b64[:4096], image_data_b64[4096:]
            chunks.append(
                _build_tgp_message(
                    a="T",
                    i=self._terminal_image_id,
                    c=cell_width,
                    r=cell_height,
                    C=1,
                    f=100,
                    m=1 if image_data_b64 else 0,
                    q=2,
                    payload=chunk,
                )
            )

        return "".join(chunks)


def query_terminal_support() -> bool:
    """Queries terminal for kitty graphics protocol support."""
    return query_tgp_terminal_support()


__all__ = ["Image", "query_terminal_support"]
