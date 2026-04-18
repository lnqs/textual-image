"""Provides a Textual `Widget` to render images as Sixels (<https://en.wikipedia.org/wiki/Sixel>) in the terminal."""

import logging
from typing import IO, ClassVar, Iterable, NamedTuple

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
from textual_image._sixel import BackgroundColor, SixelOptions, image_to_sixels
from textual_image._terminal import CellSize, get_cell_size
from textual_image._utils import StrOrBytesPath
from textual_image.widget._base import Image as BaseImage

logger = logging.getLogger(__name__)


_NULL_STYLE = Style()


class _CachedSixels(NamedTuple):
    image: StrOrBytesPath | IO[bytes] | PILImage.Image
    content_crop: Region
    content_size: Size
    terminal_sizes: CellSize
    sixel_options: SixelOptions | None
    background: BackgroundColor
    sixel_data: str

    def is_hit(
        self,
        image: StrOrBytesPath | IO[bytes] | PILImage.Image,
        content_crop: Region,
        content_size: Size,
        terminal_sizes: CellSize,
        sixel_options: SixelOptions | None,
        background: BackgroundColor,
    ) -> bool:
        return (
            image == self.image
            and content_crop == self.content_crop
            and content_size == self.content_size
            and terminal_sizes == self.terminal_sizes
            and sixel_options == self.sixel_options
            and background == self.background
        )


class _NoopRenderable:
    """Image renderable rendering nothing.

    Used by the Sixel image as placeholder.
    Rendering the Sixel renderable doesn't work with Textual as it relies on printable segments.
    Instead, Sixel data is injected into the rendering process. To keep our base class happy, we use this class
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
    """Textual `Widget` to render images as Sixels (<https://en.wikipedia.org/wiki/Sixel>) in the terminal."""

    DEFAULT_OPTIONS: ClassVar[SixelOptions | None] = None
    """Default ``SixelOptions`` used when no ``sixel_options`` is passed to ``__init__``.

    ``None`` defers to ``image_to_sixels``' own default.  Subclasses can
    override this to change the project-wide default without having to pass
    ``sixel_options`` at every call site.
    """

    def __init__(
        self,
        image: StrOrBytesPath | IO[bytes] | PILImage.Image | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        sixel_options: SixelOptions | None = None,
    ) -> None:
        """Initialize the Image widget.

        Args:
            image: The image to display.
            name: The name of the widget.
            id: The ID of the widget in the DOM.
            classes: The CSS classes for the widget.
            disabled: Whether the widget is disabled or not.
            sixel_options: Sixel encoding options.  When ``None``, falls back to
                ``self.DEFAULT_OPTIONS``.
        """
        super().__init__(
            image=image,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self._sixel_options = sixel_options if sixel_options is not None else self.DEFAULT_OPTIONS

    @override
    @BaseImage.image.setter  # type: ignore
    def image(self, value: StrOrBytesPath | IO[bytes] | PILImage.Image | None) -> None:
        super(__class__, type(self)).image.fset(self, value)  # type: ignore
        self.refresh(recompose=True)

    def compose(self) -> ComposeResult:
        """Called by Textual to create child widgets."""
        yield _ImageSixelImpl(self.image, self._sixel_options)


class _ImageSixelImpl(Widget, can_focus=False, inherit_css=False):
    """Widget implementation injecting Sixel data into the rendering process.

    This class is meant to be used only by `textual_image.widgets.sixel.Image`.
    It creates and renders Sixel data.

    It is done in this child widget to simplify the process -- this class assumes it never has to render any borders or spacings,
    but only the parent will if required by the user.
    We assume `self.region == self.content_region` in this class, which allows to the `crop` parameter in `render_lines()` directly
    on our image data without having to deal with gutters, as well as moving the cursor after rendering the sixel data to an easily
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
        sixel_options: SixelOptions | None = None,
    ) -> None:
        super().__init__()
        self.image = image
        self._sixel_options = sixel_options
        self._cached_sixels: _CachedSixels | None = None

    @override
    def render_lines(self, crop: Region) -> list[Strip]:
        # We don't render anything if the screen isn't active. Textual may try to tint the widget which leads to weird
        # effects.
        try:
            if not self.image or not self.screen.is_active:
                return []
        except NoScreen:  # if no screen, return empty list
            return []

        # Inject the sixel data. We can only do it here because we don't know the crop region before.
        terminal_sizes = get_cell_size()
        background = self._get_background_rgba()

        if self._cached_sixels and self._cached_sixels.is_hit(
            self.image, crop, self.content_size, terminal_sizes, self._sixel_options, background
        ):
            logger.debug(f"using Sixel data from cache for crop region {crop}")
            sixel_data = self._cached_sixels.sixel_data
        else:
            logger.debug(f"encoding Sixel data for crop region {crop}")

            image_data = PixelData(self.image)
            image_data = self._scale_image(image_data, terminal_sizes)
            image_data = self._crop_image(image_data, crop, terminal_sizes)

            sixel_data = self._image_to_sixels(image_data.pil_image, self._sixel_options, background=background)
            self._cached_sixels = _CachedSixels(
                self.image, crop, self.content_size, terminal_sizes, self._sixel_options, background, sixel_data
            )

        sixel_segments = self._get_sixel_segments(sixel_data)
        clear_style = self._get_clear_style()
        clear_segment = Segment(" " * crop.width, style=clear_style)
        lines = [Strip([clear_segment], cell_length=crop.width) for _ in range(crop.height - 1)]
        lines.append(Strip([clear_segment, *sixel_segments], cell_length=crop.width))
        return lines

    def _image_to_sixels(
        self,
        image: PILImage.Image,
        sixel_options: SixelOptions | None = None,
        background: BackgroundColor | None = None,
    ) -> str:
        return image_to_sixels(image, sixel_options, background)

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

    def _get_background_rgba(self) -> BackgroundColor:
        _, color = self.background_colors
        return (color.r, color.g, color.b, color.a)

    def _get_clear_style(self) -> Style:
        _, color = self.background_colors
        return Style(bgcolor=color.rich_color)

    def _get_sixel_segments(self, sixel_data: str) -> Iterable[Segment]:
        visible_region = self.screen.find_widget(self).visible_region
        return [
            Segment(
                Control.move_to(visible_region.x, visible_region.y).segment.text,
                style=_NULL_STYLE,
            ),
            Segment(sixel_data, style=_NULL_STYLE, control=((ControlType.CURSOR_FORWARD, 0),)),
            Segment(Control.move_to(visible_region.right, visible_region.bottom).segment.text, style=_NULL_STYLE),
        ]
