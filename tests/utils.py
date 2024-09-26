import io
from unittest.mock import patch

from rich.console import Console, RenderableType

from tests.data import TERMINAL_SIZES


def render(renderable: RenderableType) -> str:
    stdout = io.StringIO()
    console = Console(
        width=TERMINAL_SIZES.columns,
        height=TERMINAL_SIZES.rows,
        file=stdout,
        color_system="truecolor",
        legacy_windows=False,
        force_terminal=True,
    )
    with patch("sys.__stdout__", stdout):
        console.print(renderable)
    return stdout.getvalue()
