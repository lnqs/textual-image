from pathlib import Path

from rich.console import ConsoleDimensions, ConsoleOptions

from textual_kitty.geometry import Size
from textual_kitty.terminal import TerminalSizeInformation

TEST_IMAGE = Path(__file__).parent.parent / "textual_kitty" / "gracehopper.jpg"

SIZE_ZERO = Size(0, 0)
SIZE_TEN = Size(10, 10)

TERM_SIZE = TerminalSizeInformation(
    rows=58,
    columns=120,
    screen_width=960,
    screen_height=1044,
    cell_width=8,
    cell_height=18,
)

TERM_SIZE_NO_SCREEN = TerminalSizeInformation(
    rows=58,
    columns=120,
    screen_width=0,
    screen_height=0,
    cell_width=8,
    cell_height=12,
)

CONSOLE_OPTIONS = ConsoleOptions(
    size=ConsoleDimensions(TERM_SIZE.columns, TERM_SIZE.rows),
    legacy_windows=False,
    min_width=10,
    max_width=20,
    is_terminal=True,
    encoding="utf-8",
    max_height=20,
)
