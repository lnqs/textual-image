"""Geometry types and logic."""

from types import NoneType
from typing import NamedTuple, Tuple, cast

from textual_image._terminal import CellSize


class ImageSize(NamedTuple):
    """Image size class capable of parsing size specifications and calculating pixel and cell sizes.

    This class expects the size of the source image as `source_pixel_width` and `source_pixel_height`
    and a target width and height as `width` and `height`.
    `width` and `height` can have multiple forms:

    - If set to an integer, they describe the number of cells to be used when rendering the image.
    - If set to a string ending with `%` (e.g. `80%`) they describe the percentage of available render
      space to be used when rending the image.
    - If set to `auto` the image will be scaled to use as much as possible of the available render space
      while keeping the image's aspect ratio.
    - If set to `None` the original images dimension will be used.
    """

    source_pixel_width: int
    source_pixel_height: int
    width: int | str | None
    height: int | str | None

    def validate(self) -> None:
        """Validate the instance's size specifications.

        Raises:
            ValueError: If `width` or `height` are not valid.
        """
        self.validate_value(self.width)
        self.validate_value(self.height)

    @classmethod
    def validate_value(cls, value: int | str | None) -> None:
        """Validate a single size specification.

        Args:
            value: The size specification.

        Raises:
            ValueError: If `width` or `height` are not valid.
        """
        if isinstance(value, (int, NoneType)) or value == "auto":
            return
        if isinstance(value, str) and value.endswith("%") and value[:-1].isdecimal() and int(value[:-1]) >= 0:
            return
        raise ValueError(f"Invalid size: {value}")

    def get_cell_size(self, max_width: int, max_height: int, terminal_sizes: CellSize) -> Tuple[int, int]:
        """Calculates the render size based on original image size, size specification and terminal cell sizes.

        Args:
            max_width: The maximum available render width in cells.
            max_height: The maximum available render height in cells.
            terminal_sizes: Size information of the terminal.

        Returns:
            The render size in cells as tuple of (width, height).
        """
        self.validate()

        if self.source_pixel_height == 0 or self.source_pixel_width == 0:
            return 0, 0

        width = None
        height = None

        # Just use the original image size for dimensions that're `None`
        if self.width is None:
            width = round(self.source_pixel_width / terminal_sizes.width)
        if self.height is None:
            height = round(self.source_pixel_height / terminal_sizes.height)

        # Explicitly given cell sizes
        if isinstance(self.width, int):
            width = self.width
        if isinstance(self.height, int):
            height = self.height

        # Percentage of available space
        if isinstance(self.width, str) and self.width.endswith("%"):
            width = round(max_width / 100 * int(self.width[:-1]))
        if isinstance(self.height, str) and self.height.endswith("%"):
            height = round(max_height / 100 * int(self.height[:-1]))

        # If `width` is `auto` we use the `max_width` if we don't have a height specified,
        # but keep the ratio if `height` was set
        if self.width == "auto" and self.height is not None:
            ratio = self.source_pixel_width / self.source_pixel_height
            scaled_pixel_height: float = (height or max_height) * terminal_sizes.height
            scaled_pixel_width = scaled_pixel_height * ratio
            width = min(round(scaled_pixel_width / terminal_sizes.width), max_width)
        elif self.width == "auto":
            width = max_width

        # Same for height
        if self.height == "auto" and self.width is not None:
            ratio = self.source_pixel_width / self.source_pixel_height
            scaled_pixel_width = cast(int, width) * terminal_sizes.width
            scaled_pixel_height = scaled_pixel_width / ratio
            height = round(scaled_pixel_height / terminal_sizes.height)
        elif self.height == "auto":
            height = max_height

        # By deriving `height` from `width` in the `auto` case, `height` may exceed `max_height`,
        # which shouldn't happen when set to `auto`. Fix this my scaling down both `height` and `width`.`
        if self.width == "auto" and self.height == "auto" and cast(int, height) > max_height:
            height = max_height
            ratio = self.source_pixel_width / self.source_pixel_height
            scaled_pixel_height = height * terminal_sizes.height
            scaled_pixel_width = scaled_pixel_height * ratio
            width = round(scaled_pixel_width / terminal_sizes.width)

        return cast(Tuple[int, int], (width, height))

    def get_pixel_size(self, max_width: int, max_height: int, terminal_sizes: CellSize) -> Tuple[int, int]:
        """Calculates the pixel size to use for rendering based on original image size, size specification and terminal cell sizes.

        Args:
            max_width: The maximum available render width in cells.
            max_height: The maximum available render height in cells.
            terminal_sizes: Size information of the terminal.

        Returns:
            The render size in pixels as tuple of (width, height).
        """
        width, height = self.get_cell_size(max_width, max_height, terminal_sizes)
        return width * terminal_sizes.width, height * terminal_sizes.height
