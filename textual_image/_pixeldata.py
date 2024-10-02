"""Provides access to pixel data."""

import io
from base64 import b64encode
from contextlib import nullcontext
from pathlib import Path
from typing import ContextManager, Iterable, Iterator, Literal, Tuple

from PIL import Image as PILImage

from textual_image._utils import grouped


def ensure_image(image: str | Path | PILImage.Image) -> ContextManager[PILImage.Image]:
    """Ensures value to be an `PIL.Image.Image`.

    This function accepts either a str or `pathlib.Path` of a path to an image file or a `PIL.Image.Image` instance.
    It returns a context manager that either just provides the passed `PIL.Image.Image` instance or opens the path
    with `PIL` and provides the result.

    Args:
        image: Path to an image file or `PIL.Image.Image` instance.

    Returns:
        A context manager providing a `PIL.Image.Image` instance.
    """
    if isinstance(image, PILImage.Image):
        return nullcontext(image)
    return PILImage.open(image)


class PixelMeta:
    """Provides access to meta information of an image from a path or `PIL.Image.Image` instance."""

    def __init__(self, image: str | Path | PILImage.Image) -> None:
        """Initializes a PixelMeta.

        Args:
            image: Path to an image file or `PIL.Image.Image` instance with the image data to render.
        """
        with ensure_image(image) as opened_image:
            self.width = opened_image.width
            self.height = opened_image.height


class PixelData:
    """Provides access to pixel data from a path or `PIL.Image.Image` instance."""

    def __init__(self, image: str | Path | PILImage.Image, mode: Literal["grayscale", "rgb"] | None = None) -> None:
        """Initializes a PixelData.

        Args:
            image: Path to an image file or `PIL.Image.Image` instance with the image data to render.
            mode: Mode to convert the image into or `None` to keep the original mode.
        """
        with ensure_image(image) as opened_image:
            self._image = opened_image.copy()

        if mode == "grayscale":
            self._image = self._image.convert("L")
        elif mode == "rgb":
            self._image = self._image.convert("RGB")

    @property
    def pil_image(self) -> PILImage.Image:
        """The image as `PILImage.Image`."""
        return self._image

    @property
    def width(self) -> int:
        """The image's width."""
        return self._image.width

    @property
    def height(self) -> int:
        """The image's height."""
        return self._image.height

    def scaled(self, width: int, height: int) -> "PixelData":
        """Returns a scaled copy of this PixelData.

        Args:
            width: Width to scale to.
            height: Height to scale to.

        Returns:
            A new `PixelData` instance of the same image, scaled to (width, height).
        """
        scaled_image = self._image.resize((width, height))
        return PixelData(scaled_image)

    def cropped(self, left: int, top: int, right: int, bottom: int) -> "PixelData":
        """Returns a cropped copy of this PixelData.

        Args:
            left: Left position of the crop rectangle.
            top: Top position of the crop rectangle.
            right: Right position of the crop rectangle.
            bottom: Bottom position of the crop rectangle.

        Returns:
            A new `PixelData` instance of the same image, cropped (left, top, right, bottom).
        """
        cropped_image = self._image.crop((left, top, right, bottom))
        return PixelData(cropped_image)

    def to_base64(self) -> str:
        """Return the pixel data as base64 encoded PNG.

        Returns:
        The image data, as base64 encoded PNG.
        """
        image_buffer = io.BytesIO()
        self._image.save(image_buffer, format="png", compress_level=2)
        return b64encode(image_buffer.getvalue()).decode("ascii")

    def __iter__(self) -> Iterator[Iterable[int | Tuple[int, ...]]]:
        """Iterate the pixel data.

        Returns an `Iterator` over rows of the image.
        The rows are `Iterable`s of pixel values.

        Example:
            Iterate the image data::

            for row in PixelData("image.png"):
                for pixel in row:
                    ...  # Do something with the pixel here

        Returns:
            An `Iterator` over `Iterable`s of pixel values.
        """
        data = self._image.getdata()
        yield from grouped(data, self._image.width)
