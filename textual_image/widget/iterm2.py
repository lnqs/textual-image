"""Provides a Textual `Widget` to render images via the iTerm2 Inline Images Protocol (https://iterm2.com/documentation-images.html) in the terminal."""

import logging
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
from textual_image._terminal import CellSize, get_cell_size
from textual_image._utils import StrOrBytesPath
from textual_image.renderable.iterm2 import _build_iterm2_sequence
from textual_image.widget._base import Image as BaseImage

logger = logging.getLogger(__name__)


_NULL_STYLE = Style()


class _CachedITerm2Data(NamedTuple):
    image: StrOrBytesPath | IO[bytes] | PILImage.Image
    content_crop: Region
    content_size: Size
    terminal_sizes: CellSize
    iterm2_data: str

    def is_hit(
        self,
        image: StrOrBytesPath | IO[bytes] | PILImage.Image,
        content_crop: Region,
        content_size: Size,
        terminal_sizes: CellSize,
    ) -> bool:
        """Check if cached data matches the current parameters."""
        return (
            image == self.image
            and content_crop == self.content_crop
            and content_size == self.content_size
            and terminal_sizes == self.terminal_sizes
        )


class _NoopRenderable:
    """Image renderable rendering nothing.

    Used by the iTerm2 image as placeholder.
    Rendering the iTerm2 renderable doesn't work with Textual as it relies on printable segments.
    Instead, iTerm2 data is injected into the rendering process. To keep our base class happy, we use this class
    as renderable passed to it.
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
    """Textual `Widget` to render images via the iTerm2 Inline Images Protocol (<https://iterm2.com/documentation-images.html>) in the terminal."""

    @override
    @BaseImage.image.setter  # type: ignore
    def image(self, value: StrOrBytesPath | IO[bytes] | PILImage.Image | None) -> None:
        """Set the image to render."""
        super(__class__, type(self)).image.fset(self, value)  # type: ignore
        self.refresh(recompose=True)

    def compose(self) -> ComposeResult:
        """Called by Textual to create child widgets."""
        yield _ImageITerm2Impl(self.image)


class _ImageITerm2Impl(Widget, can_focus=False, inherit_css=False):
    """Widget implementation injecting iTerm2 image data into the rendering process.

    This class is meant to be used only by `textual_image.widget.iterm2.Image`.
    It creates and renders iTerm2 inline image data.

    It is done in this child widget to simplify the process -- this class assumes it never has to render any borders or spacings,
    but only the parent will if required by the user.
    We assume `self.region == self.content_region` in this class, which allows to use the `crop` parameter in `render_lines()` directly
    on our image data without having to deal with gutters, as well as moving the cursor after rendering the iTerm2 data to an easily
    determinable position.
    """

    DEFAULT_CSS = """
    _ImageData {
        width: 100%;
        height: 100%;
    }
    """

    @override
    def __init__(
        self,
        image: StrOrBytesPath | IO[bytes] | PILImage.Image | None = None,
    ) -> None:
        super().__init__()
        self.image = image
        self._cached_iterm2_data: _CachedITerm2Data | None = None

    @override
    def render_lines(self, crop: Region) -> list[Strip]:
        # We don't render anything if the screen isn't active. Textual may try to tint the widget which leads to weird
        # effects.
        try:
            if not self.image or not self.screen.is_active:
                return []
        except NoScreen:  # if no screen, return empty list
            return []

        # Inject the iTerm2 data. We can only do it here because we don't know the crop region before.
        terminal_sizes = get_cell_size()

        if self._cached_iterm2_data and self._cached_iterm2_data.is_hit(
            self.image, crop, self.content_size, terminal_sizes
        ):
            logger.debug(f"using iTerm2 data from cache for crop region {crop}")
            iterm2_data = self._cached_iterm2_data.iterm2_data
        else:
            logger.debug(f"encoding iTerm2 data for crop region {crop}")

            image_data = PixelData(self.image)
            image_data = self._scale_image(image_data, terminal_sizes)
            image_data = self._crop_image(image_data, crop, terminal_sizes)

            iterm2_data = _build_iterm2_sequence(
                image_data.to_base64(),
                crop.width * terminal_sizes.width,
                crop.height * terminal_sizes.height,
            )
            self._cached_iterm2_data = _CachedITerm2Data(
                self.image, crop, self.content_size, terminal_sizes, iterm2_data
            )

        iterm2_segments = self._get_iterm2_segments(iterm2_data)
        clear_style = self._get_clear_style()
        clear_segment = Segment(" " * crop.width, style=clear_style)
        lines = [Strip([clear_segment], cell_length=crop.width) for _ in range(crop.height - 1)]
        lines.append(Strip([clear_segment, *iterm2_segments], cell_length=crop.width))
        return lines

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

    def _get_iterm2_segments(self, iterm2_data: str) -> Iterable[Segment]:
        visible_region = self.screen.find_widget(self).visible_region
        return [
            Segment(
                Control.move_to(visible_region.x, visible_region.y).segment.text,
                style=_NULL_STYLE,
            ),
            Segment(iterm2_data, style=_NULL_STYLE, control=((ControlType.CURSOR_FORWARD, 0),)),
            Segment(Control.move_to(visible_region.right, visible_region.bottom - 2).segment.text, style=_NULL_STYLE),
        ]

    def _get_clear_style(self) -> Style:
        _, color = self.background_colors
        return Style(bgcolor=color.rich_color)
