from pathlib import Path

from rich.console import ConsoleDimensions, ConsoleOptions

from textual_kitty.terminal import TerminalSizes

TEST_IMAGE = Path(__file__).parent.parent / "textual_kitty" / "gracehopper.jpg"

TERMINAL_SIZES = TerminalSizes(
    rows=58,
    columns=120,
    screen_width=960,
    screen_height=928,
    cell_width=8,
    cell_height=16,
)

CONSOLE_OPTIONS = ConsoleOptions(
    size=ConsoleDimensions(TERMINAL_SIZES.columns, TERMINAL_SIZES.rows),
    legacy_windows=False,
    min_width=10,
    max_width=20,
    is_terminal=True,
    encoding="utf-8",
    max_height=20,
)
