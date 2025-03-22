import io
import pathlib
from typing import IO
from unittest.mock import patch

from rich.console import Console, RenderableType

from tests.data import CONSOLE_OPTIONS


def render(renderable: RenderableType) -> str:
    stdout = io.StringIO()
    console = Console(
        width=CONSOLE_OPTIONS.size.width,
        height=CONSOLE_OPTIONS.size.height,
        file=stdout,
        color_system="truecolor",
        legacy_windows=False,
        force_terminal=True,
    )
    with patch("sys.__stdout__", stdout):
        console.print(renderable)
    return stdout.getvalue()


class NonSeekableBytesIO(io.BytesIO):
    def seekable(self) -> bool:
        return False

    def seek(self, pos: int, whence: int = 0, /) -> int:
        raise io.UnsupportedOperation("seek not allowed")


def load_non_seekable_bytes_io(path: pathlib.Path) -> IO[bytes]:
    with open(path, "rb") as file:
        data = file.read()

    return NonSeekableBytesIO(data)
