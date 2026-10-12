"""Provides a Textual `Widget` implementing basic kitty graphics protocol placement."""

import logging
from itertools import count
from random import randint
from typing import IO, Iterable, NamedTuple

from PIL import Image as PILImage
from rich.console import Console, ConsoleOptions, RenderResult
from rich.control import Control
from rich.measure import Measurement
from rich.segment import ControlType, Segment
from rich.style import Style
from textual.app import ComposeResult
from textual.dom import NoScreen
from textual.geometry import Region, Size
from textual.strip import Strip
from textual.widget import Widget
from typing_extensions import override

from textual_image._geometry import ImageSize
from textual_image._pixeldata import PixelData
from textual_image._terminal import CellSize, TerminalError, get_cell_size
from textual_image._utils import StrOrBytesPath
from textual_image.renderable.tgp import _send_tgp_message
from textual_image.widget._base import Image as BaseImage

logger = logging.getLogger(__name__)


_NULL_STYLE = Style()

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


class _CachedPlacement(NamedTuple):
    image: StrOrBytesPath | IO[bytes] | PILImage.Image
    content_crop: Region
    content_size: Size
    terminal_sizes: CellSize
    control_data: str

    def is_hit(
        self,
        image: StrOrBytesPath | IO[bytes] | PILImage.Image,
        content_crop: Region,
        content_size: Size,
        terminal_sizes: CellSize,
    ) -> bool:
        return (
            image == self.image
            and content_crop == self.content_crop
            and content_size == self.content_size
            and terminal_sizes == self.terminal_sizes
        )


class _NoopRenderable:
    """Image renderable rendering nothing.

    Used by the kitty widget as placeholder.
    Rendering from rich renderables does not work with Textual for this implementation,
    as we need crop and viewport information available only in `render_lines()`.
    """

    def __init__(
        self,
        image: StrOrBytesPath | IO[bytes] | PILImage.Image,
        width: int | str | None = None,
        height: int | str | None = None,
    ) -> None:
        pass

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield Segment("")

    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
        return Measurement(0, 0)

    def cleanup(self) -> None:
        pass


class Image(BaseImage, Renderable=_NoopRenderable):
    """Textual `Widget` using basic kitty graphics protocol image placement."""

    def compose(self) -> ComposeResult:
        """Called by Textual to create child widgets."""
        yield _ImageKittyImpl()


class _ImageKittyImpl(Widget, can_focus=False, inherit_css=False):
    """Widget implementation injecting kitty graphics protocol control data.

    This class is meant to be used only by `textual_image.widget.kitty.Image`.
    """

    DEFAULT_CSS = """
    _ImageKittyImpl {
        width: 100%;
        height: 100%;
    }
    """

    _image_id_counter = count(randint(1, 2**32))

    @override
    def __init__(self) -> None:
        super().__init__()
        self._cached_placement: _CachedPlacement | None = None
        self._terminal_image_id = next(self._image_id_counter)

    def on_unmount(self) -> None:
        try:
            _send_tgp_message(a="d", d="I", i=self._terminal_image_id, q=2)
        except TerminalError:
            pass

    @override
    def render_lines(self, crop: Region) -> list[Strip]:
        assert isinstance(self.parent, Image)

        try:
            if not self.parent.image or not self.screen.is_active:
                return []
        except NoScreen:
            return []

        terminal_sizes = get_cell_size()

        if self._cached_placement and self._cached_placement.is_hit(
            self.parent.image, crop, self.content_size, terminal_sizes
        ):
            logger.debug(f"using kitty placement data from cache for crop region {crop}")
            control_data = self._cached_placement.control_data
        else:
            logger.debug(f"encoding kitty placement data for crop region {crop}")
            image_data = PixelData(self.parent.image)
            image_data = self._scale_image(image_data, terminal_sizes)
            image_data = self._crop_image(image_data, crop, terminal_sizes)
            control_data = self._image_to_control_data(image_data, crop)
            self._cached_placement = _CachedPlacement(
                self.parent.image,
                crop,
                self.content_size,
                terminal_sizes,
                control_data,
            )

        kitty_segments = self._get_kitty_segments(control_data)
        clear_style = self._get_clear_style()
        clear_segment = Segment(" " * crop.width, style=clear_style)
        lines = [Strip([clear_segment], cell_length=crop.width) for _ in range(crop.height - 1)]
        lines.append(Strip([clear_segment, *kitty_segments], cell_length=crop.width))
        return lines

    def _image_to_control_data(self, image_data: PixelData, crop: Region) -> str:
        base64_data = image_data.to_base64()
        chunks: list[str] = []
        while base64_data:
            chunk, base64_data = base64_data[:4096], base64_data[4096:]
            chunks.append(
                _build_tgp_message(
                    a="T",
                    i=self._terminal_image_id,
                    c=crop.width,
                    r=crop.height,
                    C=1,
                    f=100,
                    m=1 if base64_data else 0,
                    q=2,
                    payload=chunk,
                )
            )

        return "".join(chunks)

    def _scale_image(self, image_data: PixelData, terminal_sizes: CellSize) -> PixelData:
        assert isinstance(self.parent, Image)

        styled_width, styled_height = self.parent._get_styled_size()
        image_size = ImageSize(image_data.width, image_data.height, width=styled_width, height=styled_height)
        pixel_width, pixel_height = image_size.get_pixel_size(
            self.content_size.width, self.content_size.height, terminal_sizes
        )

        return image_data.scaled(pixel_width, pixel_height)

    def _crop_image(self, image: PixelData, crop: Region, terminal_sizes: CellSize) -> PixelData:
        crop_pixels_left = crop.x * terminal_sizes.width
        crop_pixels_top = crop.y * terminal_sizes.height
        crop_pixels_right = crop.right * terminal_sizes.width
        crop_pixels_bottom = crop.bottom * terminal_sizes.height

        return image.cropped(crop_pixels_left, crop_pixels_top, crop_pixels_right, crop_pixels_bottom)

    def _get_kitty_segments(self, control_data: str) -> Iterable[Segment]:
        visible_region = self.screen.find_widget(self).visible_region
        return [
            Segment(
                Control.move_to(visible_region.x, visible_region.y).segment.text,
                style=_NULL_STYLE,
            ),
            Segment(control_data, style=_NULL_STYLE, control=((ControlType.CURSOR_FORWARD, 0),)),
            Segment(Control.move_to(visible_region.right, visible_region.bottom).segment.text, style=_NULL_STYLE),
        ]

    def _get_clear_style(self) -> Style:
        _, color = self.background_colors
        return Style(bgcolor=color.rich_color)
