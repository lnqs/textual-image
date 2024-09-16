"""Provides functionality to render images with Rich as unicode characters."""

import logging
from pathlib import Path
from typing import override

from PIL import Image as PILImage

from textual_kitty.geometry import Size
from textual_kitty.renderable._base import _Base
from textual_kitty.terminal import TerminalSizeInformation

logger = logging.getLogger(__name__)


class _FallbackBase(_Base):
    """Rich renderable to render images in terminal.

    This Renderable renders an image as unicode characters. Used as fallback if other protocols are not available.
    """

    @override
    def __init__(self, image: str | Path | PILImage.Image, width: int | None = None) -> None:
        super().__init__(image, width)
        self._prepared_image: PILImage.Image | None = None

    @override
    def is_prepared(self, size: Size, term_size: TerminalSizeInformation) -> bool:
        if self._prepared_image and self._prepared_image.size == self._calculate_image_size_for_render_size(
            size, term_size
        ):
            return True
        return False

    @override
    def prepare(self, size: Size, term_size: TerminalSizeInformation) -> None:
        logger.debug("Scaling fallback image for rendering")
        self._prepared_image = self._prepare_image(size, term_size)

    @override
    async def prepare_async(self, size: Size, term_size: TerminalSizeInformation) -> None:
        logger.debug("Scaling fallback image for rendering asynchrounouly")
        self._prepared_image = await self._run_in_thread(lambda: self._prepare_image(size, term_size))

    def _prepare_image(self, size: Size, term_size: TerminalSizeInformation) -> PILImage.Image:
        raise NotImplementedError()

    def _calculate_image_size_for_render_size(self, render_size: Size, term_size: TerminalSizeInformation) -> Size:
        raise NotImplementedError()
