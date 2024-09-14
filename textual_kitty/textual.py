"""Provides functionality to render images with Textual."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Awaitable, Callable

from PIL import Image as PILImage
from rich.console import ConsoleRenderable, RichCast
from textual import work
from textual.geometry import Size
from textual.widget import Widget
from textual.worker import Worker

from textual_kitty.rich import Image as ImageRenderable
from textual_kitty.rich import ImageSize


class _AsyncImageRenderable(ImageRenderable):
    image_processing_executor = ThreadPoolExecutor()

    def __init__(
        self,
        image: str | Path | PILImage.Image,
        async_runner: Callable[[Callable[[], Awaitable[None]]], Worker[None]],
    ) -> None:
        super().__init__(image)
        self._async_runner = async_runner

    def _prepare_terminal(self, size: ImageSize) -> None:
        self._async_runner(lambda: self._prepare_terminal_async(size))

    async def _prepare_terminal_async(self, size: ImageSize) -> None:
        self.delete_image_from_terminal()

        # PIL released the GIL, so this should actually parallelize
        image_data = await asyncio.get_running_loop().run_in_executor(
            _AsyncImageRenderable.image_processing_executor,
            lambda: self._get_encoded_image_data(size),
        )

        self._send_image_to_terminal(image_data)
        self._create_placement(size)

        self._placement_size = size


class Image(Widget, inherit_bindings=False):
    """Textual `Widget` to render images in termnial.

    This `Widget` uses the Terminal Graphics Protocol (<https://sw.kovidgoyal.net/kitty/graphics-protocol/>)
    to render images, so a compatible terminal (like Kitty) is required.
    """

    DEFAULT_CSS = """
    Image {
        height: auto;
    }
    """

    def __init__(
        self,
        image: str | Path | PILImage.Image | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        load_async: bool = False,
    ) -> None:
        """Initialize an `Image`.

        Args:
            image: Path to image or PIL.Image.Image instance for image to display.
            name: The name of the widget.
            id: The ID of the widget in the DOM.
            classes: The CSS classes for the widget.
            disabled: Whether the widget is disabled or not.
            load_async: Process image data asynchronously.
                If True, the first render of the image (and subsequent after a resize) will not actually render the
                image, but start processing the image data and sending it to the terminal asynchronously. The Widget
                will update itself after this is done to show the image. A loading indicator is shown during
                processing. This helps keeping the app responsive if large images are passed to this class.
                But it does come with with the overhead of double the update cycles and running asynchronously tasks.
        """
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self._renderable: ImageRenderable | None = None
        self._load_async = load_async
        self.image = image

    @property
    def image(self) -> str | Path | PILImage.Image | None:
        """The actual image to display.

        Can be either a `str` with a file path, a `pathlib.Path` to the file with the image data, or a `PIL.Image.Image`
        instance
        Setting this property will cause the widget to re-render itself to display the new image.

        Returns:
            The image to render as passed in constructor or set to this property
        """
        return self._image

    @image.setter
    def image(self, value: str | Path | PILImage.Image | None) -> None:
        if self._renderable:
            self._renderable.delete_image_from_terminal()
            self._renderable = None

        self._image = value.copy() if isinstance(value, PILImage.Image) else value

        if self._image:
            self._renderable = (
                _AsyncImageRenderable(image=self._image, async_runner=self._run_async)
                if self._load_async
                else ImageRenderable(self._image)
            )

        self.clear_cached_dimensions()
        self.refresh()

    def on_unmount(self) -> None:
        """Called by Textual when the `Image` gets unmountet.

        Cleans up the image data from the terminal
        """
        if self._renderable:
            self._renderable.delete_image_from_terminal()

    def get_content_width(self, container: Size, _viewport: Size) -> int:
        """Called by Textual when the preferred render width.

        Args:
            container: Size of the parent container
            _viewport: Viewport size. Not used.

        Returns:
            The preferred render width
        """
        if not self._renderable:
            return 0

        width, _ = self._renderable._calculate_render_size(container.width, container.height)
        return width

    def get_content_height(self, container: Size, _viewport: Size, width: int) -> int:
        """Called by Textual when the preferred render height.

        Args:
            container: Size of the parent container
            _viewport: Viewport size. Not used.
            width: Render width
        Returns:
            The preferred render height
        """
        if not self._renderable:
            return 0

        _, height = self._renderable._calculate_render_size(width, container.height)
        return height

    def render(self) -> ConsoleRenderable | RichCast | str:
        """Called by Textual to render the `Image`.

        Returns:
            A rich renderable that renders the image
        """
        if not self._renderable:
            return ""

        # With async loading, we might not have a suitable placement yet. Show loading indicator in this case.
        self.loading = self._renderable._placement_size != self.container_size
        return self._renderable

    @work(exclusive=True)
    async def _run_async(self, fn: Callable[[], Awaitable[None]]) -> None:
        await fn()
        self.refresh()
