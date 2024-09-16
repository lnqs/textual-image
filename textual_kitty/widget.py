"""Provides functionality to render images with Textual."""

from pathlib import Path
from typing import Type

from PIL import Image as PILImage
from rich.console import ConsoleRenderable, RichCast
from textual import work
from textual.geometry import Size
from textual.widget import Widget

from textual_kitty.geometry import Size as ImageSize
from textual_kitty.renderable import Image as ImageRenderable
from textual_kitty.renderable._base import _Base as ImageRenderableBase
from textual_kitty.terminal import TerminalSizeInformation, get_terminal_size_info


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
        image_renderable_type: Type[ImageRenderableBase] = ImageRenderable,
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
            image_renderable_type: The image renderable type to use. Defaults to the auto determined best available
                type, but can be explicitly overwritten.
        """
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self._image_renderable_type: Type[ImageRenderableBase] = image_renderable_type
        self._renderable: ImageRenderableBase | None = None
        self._load_async = load_async
        self.image = image

    @property
    def image(self) -> str | Path | PILImage.Image | None:
        """The actual image to display.

        Can be either a `str` with a file path, a `pathlib.Path` to the file with the image data, or a `PIL.Image.Image`
        instance.
        Setting this property will cause the widget to re-render itself to display the new image.

        Returns:
            The image to render as passed in constructor or set to this property
        """
        return self._image

    @image.setter
    def image(self, value: str | Path | PILImage.Image | None) -> None:
        if self._renderable:
            self._renderable.cleanup()
            self._renderable = None

        self._image = value.copy() if isinstance(value, PILImage.Image) else value

        if self._image:
            self._renderable = self._image_renderable_type(self._image)

        self.clear_cached_dimensions()
        self.refresh()

    def on_unmount(self) -> None:
        """Called by Textual when the `Image` gets unmountet.

        Cleans up the image data from the terminal
        """
        if self._renderable:
            self._renderable.cleanup()

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

        term_size = get_terminal_size_info()
        width, _ = self._renderable.get_render_size(ImageSize(container.width, container.height), term_size)
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

        term_size = get_terminal_size_info()
        _, height = self._renderable.get_render_size(ImageSize(width, container.height), term_size)
        return height

    def render(self) -> ConsoleRenderable | RichCast | str:
        """Called by Textual to render the `Image`.

        Returns:
            A rich renderable that renders the image
        """
        if not self._renderable:
            return ""

        # The Renderable prepares itself if necessary, if we don't need the async functionality
        term_size = get_terminal_size_info()
        if self._load_async and not self._renderable.is_prepared(ImageSize(*self.content_size), term_size):
            self._trigger_prepare_async(self.content_size, term_size)
            self.loading = True
            return ""

        self.loading = False
        return self._renderable

    @work(exclusive=True)
    async def _trigger_prepare_async(self, size: Size, term_size: TerminalSizeInformation) -> None:
        if self._renderable:
            await self._renderable.prepare_async(ImageSize(*size), term_size)
            self.refresh()
