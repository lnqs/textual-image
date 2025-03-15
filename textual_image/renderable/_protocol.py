from typing import IO, Protocol

from PIL import Image as PILImage
from rich.console import Console, ConsoleOptions, RenderResult
from rich.measure import Measurement

from textual_image._utils import StrOrBytesPath


class ImageRenderable(Protocol):
    """Protocol for `Image` renderables."""

    def __init__(
        self,
        image: StrOrBytesPath | IO[bytes] | PILImage.Image,
        width: int | str | None = None,
        height: int | str | None = None,
    ) -> None: ...
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult: ...
    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement: ...
    def cleanup(self) -> None: ...
