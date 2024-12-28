"""Provides a Textual `Widget` to render images in the terminal."""

from pathlib import Path
from typing import Literal, Tuple, Type, cast

from PIL import Image as PILImage
from textual.app import RenderResult
from textual.css.styles import RenderStyles
from textual.geometry import Size
from textual.widget import Widget
from typing_extensions import override

from textual_image._geometry import ImageSize
from textual_image._pixeldata import PixelMeta
from textual_image._terminal import get_cell_size
from textual_image.renderable._protocol import ImageRenderable


class Image(Widget):
    """Textual `Widget` to render images in the terminal."""

    _Renderable: Type[ImageRenderable]

    @override
    def __init_subclass__(
        cls,
        Renderable: Type[ImageRenderable],
        can_focus: bool | None = None,
        can_focus_children: bool | None = None,
        inherit_css: bool = True,
        inherit_bindings: bool = True,
    ) -> None:
        """Initializes sub classes.

        Args:
            cls: The sub class to initialize.
            Renderable: The image renderable the subclass is supposed to use.
            can_focus: Is the Widget can become focussed.
            can_focus_children: If the Widget's children can become focussed.
            inherit_css: If CSS should be inherited.
            inherit_bindings: If bindings should be inherited.
        """
        super().__init_subclass__(can_focus, can_focus_children, inherit_css, inherit_bindings)
        cls._Renderable = Renderable

    def __init__(
        self,
        image: str | Path | PILImage.Image | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Initializes the `Image`.

        Args:
            image: Path to an image file or `PIL.Image.Image` instance with the image data to render.
            name: The name of the widget.
            id: The ID of the widget in the DOM.
            classes: The CSS classes for the widget.
            disabled: Whether the widget is disabled or not.
        """
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self._renderable: ImageRenderable | None = None
        self._image: str | Path | PILImage.Image | None = None
        self._image_width: int = 0
        self._image_height: int = 0

        self.image = image

    @property
    def image(self) -> str | Path | PILImage.Image | None:
        """The image to render.

        Path to an image file or `PIL.Image.Image` instance with the image data to render.
        """
        return self._image

    @image.setter
    def image(self, value: str | Path | PILImage.Image | None) -> None:
        if self._renderable:
            self._renderable.cleanup()
            self._renderable = None

        self._image = value

        if value:
            pixel_meta = PixelMeta(value)
            self._image_width = pixel_meta.width
            self._image_height = pixel_meta.height
        else:
            self._image_width = 0
            self._image_height = 0

        self.refresh(layout=True, recompose=True)

    @override
    def render(self) -> RenderResult:
        if not self._image:
            return ""

        if self._renderable:
            self._renderable.cleanup()
            self._renderable = None

        self._renderable = self._Renderable(self._image, *self._get_styled_size())
        return self._renderable

    @override
    def get_content_width(self, container: Size, viewport: Size) -> int:
        styled_width, styled_height = self._get_styled_size()
        terminal_sizes = get_cell_size()
        # If Textual doesn't know the container height yet it's reported as 0. To prevent our
        # image to be size 0x0 if set to auto, pass a really high number in that case.
        width, _ = ImageSize(
            self._image_width, self._image_height, width=styled_width, height=styled_height
        ).get_cell_size(container.width, container.height or 2**32, terminal_sizes)
        return width

    @override
    def get_content_height(self, container: Size, viewport: Size, width: int) -> int:
        styled_width, styled_height = self._get_styled_size()
        terminal_sizes = get_cell_size()
        _, height = ImageSize(
            self._image_width, self._image_height, width=styled_width, height=styled_height
        ).get_cell_size(width, container.height or 2**32, terminal_sizes)
        return height

    def _get_styled_size(self) -> Tuple[None | Literal["auto"] | int, None | Literal["auto"] | int]:
        width = self._get_styled_dimension(self.styles, "width")
        height = self._get_styled_dimension(self.styles, "height")
        return width, height

    def _get_styled_dimension(
        self, styles: RenderStyles, dimension: Literal["width", "height"]
    ) -> None | Literal["auto"] | int:
        style = getattr(styles, dimension)
        if style is None:
            return None
        elif style.is_auto:
            return "auto"
        else:
            return cast(int, getattr(self.content_size, dimension))
