from importlib.util import find_spec
from pathlib import Path

from rich.console import ConsoleDimensions, ConsoleOptions

from textual_image._terminal import CellSize

TEXTUAL_ENABLED = bool(find_spec("textual"))

TEST_IMAGE = Path(__file__).parent.parent / "textual_image" / "gracehopper.jpg"

CELL_SIZE = CellSize(
    width=10,
    height=20,
)

CONSOLE_OPTIONS = ConsoleOptions(
    size=ConsoleDimensions(120, 58),
    legacy_windows=False,
    min_width=10,
    max_width=20,
    is_terminal=True,
    encoding="utf-8",
    max_height=20,
)
