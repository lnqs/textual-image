"""Base class for rich image Renderables."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from pathlib import Path
from typing import Callable, TypeVar

from PIL import Image as PILImage
from rich.console import Console, ConsoleOptions, RenderResult
from rich.measure import Measurement

from textual_kitty.geometry import Size
from textual_kitty.terminal import TerminalSizeInformation, get_terminal_size_info

T = TypeVar("T")


class _Base:
    _thread_executor = ThreadPoolExecutor()

    def __init__(self, image: str | Path | PILImage.Image, width: int | None = None) -> None:
        """Initialize an `Image`.

        Args:
            image: The image to display, either as path or `Pillow.Image.Image` object
            width: Fixed width in cells to render the image in. Will use available width if not set.
        """
        self.image = image
        self.width = width

    def is_prepared(self, size: Size, term_size: TerminalSizeInformation) -> bool:
        """Returns if this image is prepared for rendering in a specific size.

        This means that image data is loaded and scaled, send to the terminal, etc.
        Whatever the image implementation needs to prepare to be able to render the image.

        This method is used by the Textual Widget to decide if async preparation has to be
        triggered.

        Args:
            size: The size to check the preparation against
            term_size: Size information about the terminal

        Returns:
            True if the image is prepared for rendering, False if not.
        """
        raise NotImplementedError()

    def prepare(self, size: Size, term_size: TerminalSizeInformation) -> None:
        """Prepare the image for rendering in a specific size.

        This means to load and scale image data, send to the terminal, etc.
        Whatever the image implementation needs to prepare to be able to render the image.

        This method is called internally before the actual rendering happens.

        Args:
            size: The size to check the preparation against
            term_size: Size information about the terminal
        """
        raise NotImplementedError()

    async def prepare_async(self, size: Size, term_size: TerminalSizeInformation) -> None:
        """Prepare the image for rendering in a specific size asynchronously.

        This means to load and scale image data, send to the terminal, etc.
        Whatever the image implementation needs to prepare to be able to render the image.

        It is supposed to perform the same tasks as `prepare`, but in an async way.

        This method is called by the Textual `Image` widget if `load_async` is set to
        improve the responsiveness of the app.

        Args:
            size: The size to check the preparation against
            term_size: Size information about the terminal
        """
        raise NotImplementedError()

    def _render(self) -> RenderResult:
        """Render the image.

        Returns:
            A rich `RenderResult` with the image data.
        """
        raise NotImplementedError()

    def cleanup(self) -> None:
        """Free image data from terminal.

        Depending on the graphics implementation, this may clean up data or is a no-op
        """
        pass

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        """Called by rich to render the `Image`.

        Args:
            console: The `Console` instance to render to
            options: Options for rendering, i.e. available size information
        """
        term_size = get_terminal_size_info()
        size = self.get_render_size(Size(options.max_width, options.max_height), term_size)
        if not self.is_prepared(size, term_size):
            self.prepare(size, term_size)
        yield from self._render()

    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
        """Called by rich to get the render size without actually rendering the `Image`.

        Args:
            console: The `Console` instance to render to
            options: Options for rendering, i.e. available size information
        """
        term_size = get_terminal_size_info()
        size = self.get_render_size(Size(options.max_width, options.max_height), term_size)
        return Measurement(size.width, size.width)

    def get_render_size(self, max_size: Size, term_size: TerminalSizeInformation) -> Size:
        """Calculate the render size of the image in cells.

        This method takes the maximum available size and terminal size to calculate the size (in cells)
        to render the image in. It respects the width parameter if passed to the constructor and keeps
        the aspect ratio of the image.

        Args:
            max_size: Maximum width and height the rendered image may have
            term_size: Terminal size information
        Returns:
            The size the image will be rendered in
        """
        width = max_size.width
        if self.width is not None:
            width = self.width
        if width < 0:
            return Size(0, 0)

        image_pixel_width, image_pixel_height = self.original_image_size
        ratio = image_pixel_width / image_pixel_height
        scaled_pixel_width: float = width * term_size.cell_width
        scaled_pixel_height = scaled_pixel_width / ratio
        height = int(scaled_pixel_height / term_size.cell_height)

        if max_size.height and height > max_size.height:
            height = max_size.height
            scaled_pixel_height = height * term_size.cell_height
            scaled_pixel_width = scaled_pixel_height * ratio
            width = int(scaled_pixel_width / term_size.cell_width)

        return Size(width, height)

    @property
    def original_image_size(self) -> Size:
        """Returns the original size of the image data passed in in pixels.

        Returns:
            The original size of the image data passed in in pixels
        """
        with (
            nullcontext(self.image)  # type: ignore
            if isinstance(self.image, PILImage.Image)
            else PILImage.open(self.image)
        ) as image:
            return Size(*image.size)

    async def _run_in_thread(self, func: Callable[[], T]) -> T:
        """Execute a function in a worker thread.

        This method runs a function in a thread pool worker.
        It's up to derived classed what to use this for, but generally image processing in prepare_async()
        is offloaded to a thread, as Pillow releases the GIL and does allow actual parallelization.

        Args:
            func: The function to run in a worker thread
        Returns:
            The return value of `func`
        """
        return await asyncio.get_running_loop().run_in_executor(_Base._thread_executor, func)
