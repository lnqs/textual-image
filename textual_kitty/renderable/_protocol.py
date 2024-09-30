from pathlib import Path
from typing import Protocol

from PIL import Image as PILImage
from rich.console import Console, ConsoleOptions, RenderResult
from rich.measure import Measurement


class ImageRenderable(Protocol):
    """Protocol for `Image` renderables."""

    def __init__(
        self, image: str | Path | PILImage.Image, width: int | str | None = None, height: int | str | None = None
    ) -> None: ...
    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult: ...
    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement: ...
    def cleanup(self) -> None: ...
