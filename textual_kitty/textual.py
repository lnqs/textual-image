from pathlib import Path

from PIL import Image as PILImage
from rich.console import ConsoleRenderable, RichCast
from textual.geometry import Size
from textual.widget import Widget

from textual_kitty.rich import Image as ImageRenderable


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
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self._renderable: ImageRenderable | None = None
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
            self._renderable = ImageRenderable(self._image)

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
        return self._renderable or ""
