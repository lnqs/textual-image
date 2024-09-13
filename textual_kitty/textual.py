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


class AsyncImageRenderable(ImageRenderable):
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
            AsyncImageRenderable.image_processing_executor,
            lambda: self._get_encoded_image_data(size),
        )

        self._send_image_to_terminal(image_data)
        self._create_placement(size)

        self._placement_size = size


class Image(Widget, inherit_bindings=False):
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
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self._renderable: ImageRenderable | None = None
        self._load_async = load_async
        self.image = image

    @property
    def image(self) -> str | Path | PILImage.Image | None:
        return self._image

    @image.setter
    def image(self, value: str | Path | PILImage.Image | None) -> None:
        if self._renderable:
            self._renderable.delete_image_from_terminal()
            self._renderable = None

        self._image = value.copy() if isinstance(value, PILImage.Image) else value

        if self._image:
            self._renderable = (
                AsyncImageRenderable(image=self._image, async_runner=self._run_async)
                if self._load_async
                else ImageRenderable(self._image)
            )

        self.clear_cached_dimensions()
        self.refresh()

    def on_unmount(self) -> None:
        if self._renderable:
            self._renderable.delete_image_from_terminal()

    def get_content_width(self, container: Size, _viewport: Size) -> int:
        if not self._renderable:
            return 0

        width, _ = self._renderable._calculate_render_size(
            container.width, container.height
        )
        return width

    def get_content_height(self, container: Size, _viewport: Size, width: int) -> int:
        if not self._renderable:
            return 0

        _, height = self._renderable._calculate_render_size(width, container.height)
        return height

    def render(self) -> ConsoleRenderable | RichCast | str:
        if not self._renderable:
            return ""

        # With async loading, we might not have a suitable placement yet. Show loading indicator in this case.
        self.loading = self._renderable._placement_size != self.container_size
        return self._renderable

    @work(exclusive=True)
    async def _run_async(self, fn: Callable[[], Awaitable[None]]) -> None:
        await fn()
        self.refresh()
