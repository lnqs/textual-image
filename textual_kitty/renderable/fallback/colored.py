"""Provides functionality to render images with Rich as colored unicode characters."""

from contextlib import nullcontext
from typing import Tuple, cast, override

from PIL import Image as PILImage
from rich.color import Color
from rich.color_triplet import ColorTriplet
from rich.console import RenderResult
from rich.segment import Segment
from rich.style import Style

from textual_kitty.geometry import Size
from textual_kitty.renderable.fallback._base import _FallbackBase
from textual_kitty.terminal import TerminalSizeInformation


class Image(_FallbackBase):
    """Rich renderable to render images in terminal.

    This Renderable renders an image as colored unicode characters. Used as fallback if other protocols are not available.
    """

    @override
    def _prepare_image(self, size: Size, term_size: TerminalSizeInformation) -> PILImage.Image:
        with nullcontext(self.image) if isinstance(self.image, PILImage.Image) else PILImage.open(self.image) as image:  # type: ignore
            return cast(PILImage.Image, image.resize(self._calculate_image_size_for_render_size(size, term_size)))

    @override
    def _calculate_image_size_for_render_size(self, render_size: Size, term_size: TerminalSizeInformation) -> Size:
        return Size(int(render_size.width), int(render_size.height / (term_size.cell_width / term_size.cell_height)))

    @override
    def _render(self) -> RenderResult:
        if not self._prepared_image:
            return

        for y in range(0, self._prepared_image.height, 2):
            for x in range(self._prepared_image.width):
                upper = self._get_pixel(x, y)
                lower = self._get_pixel(x, y + 1) if y + 1 < self._prepared_image.height else None
                yield Segment("▀", style=Style(color=upper, bgcolor=lower))
            yield Segment("\n")

    def _get_pixel(self, x: int, y: int) -> Color:
        if not self._prepared_image:
            return Color.default()

        data = self._prepared_image.getpixel((x, y))
        return Color.from_triplet(ColorTriplet(*cast(Tuple[int, int, int], data)))
