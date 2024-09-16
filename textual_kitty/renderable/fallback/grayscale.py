"""Provides functionality to render images with Rich as unicode characters."""

from contextlib import nullcontext
from typing import cast, override

from PIL import Image as PILImage
from rich.console import RenderResult
from rich.segment import Segment

from textual_kitty.geometry import Size
from textual_kitty.renderable.fallback._base import _FallbackBase
from textual_kitty.terminal import TerminalSizeInformation

CHARACTERS = [
    "█",  # FULL BLOCK
    "▓",  # DARK SHADE
    "▒",  # MEDIUM SHADE
    "░",  # LIGHT SHADE
    " ",  # SPACE
]

CHARACTER_LOOKUP = {int(255 / len(CHARACTERS) * i): c for i, c in enumerate(CHARACTERS)}


class Image(_FallbackBase):
    """Rich renderable to render images in terminal.

    This Renderable renders an image as unicode characters. Used as fallback if other protocols are not available.
    """

    @override
    def _prepare_image(self, size: Size, term_size: TerminalSizeInformation) -> PILImage.Image:
        with nullcontext(self.image) if isinstance(self.image, PILImage.Image) else PILImage.open(self.image) as image:  # type: ignore
            image = image.resize(self._calculate_image_size_for_render_size(size, term_size))
            image = image.convert("L")
            return cast(PILImage.Image, image)

    @override
    def _calculate_image_size_for_render_size(self, render_size: Size, term_size: TerminalSizeInformation) -> Size:
        return Size(
            int(render_size.width), int(render_size.height / 2 / (term_size.cell_width / term_size.cell_height))
        )

    @override
    def _render(self) -> RenderResult:
        if not self._prepared_image:
            return

        for y in range(0, self._prepared_image.height):
            for x in range(self._prepared_image.width):
                character = self._get_pixel(x, y)
                yield Segment(character)
            yield Segment("\n")

    def _get_pixel(self, x: int, y: int) -> str:
        if not self._prepared_image:
            return " "

        pixel = cast(int, self._prepared_image.getpixel((x, y)))
        brightness = 255 - pixel
        index = int(255 / len(CHARACTER_LOOKUP)) * int(brightness / int(255 / len(CHARACTER_LOOKUP)))
        return CHARACTER_LOOKUP[index]
