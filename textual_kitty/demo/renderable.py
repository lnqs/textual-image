#!/usr/bin/env python

"""Showcase textual-kitty's Rich renderables."""

from argparse import ArgumentParser
from enum import Enum
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from textual_kitty.renderable import (
    HalfcellImage as HalfcellRenderable,
)
from textual_kitty.renderable import (
    Image as AutoRenderable,
)
from textual_kitty.renderable import (
    SixelImage as SixelRenderable,
)
from textual_kitty.renderable import (
    TGPImage as TGPRenderable,
)
from textual_kitty.renderable import (
    UnicodeImage as UnicodeRenderable,
)

TEST_IMAGE = Path(__file__).parent / ".." / "gracehopper.jpg"


class RenderingMethods(Enum):
    """Available rendering methods."""

    auto = AutoRenderable
    tgp = TGPRenderable
    sixel = SixelRenderable
    halfcell = HalfcellRenderable
    unicode = UnicodeRenderable


def run(rendering_method: RenderingMethods = RenderingMethods.auto) -> None:
    """Showcase textual-kitty's Rich renderables."""
    Image = rendering_method.value

    table = Table.grid(padding=1, pad_edge=True)
    table.title = "textual-kitty's features"
    table.add_column("Feature", no_wrap=True, justify="center", style="bold red")
    table.add_column("Demonstration")

    sizings_table = Table.grid(padding=1, collapse_padding=True)
    sizings_table.add_row(
        Image(TEST_IMAGE, width=30, height="auto"),
        Image(TEST_IMAGE, width=20, height="auto"),
        Image(TEST_IMAGE, width=10, height="auto"),
    )
    table.add_row("Different sizing options", sizings_table)

    sizings2_table = Table.grid(padding=1, collapse_padding=True)
    sizings2_table.add_row(
        Image(TEST_IMAGE, width=10, height=15),
        Image(TEST_IMAGE, width=20, height=15),
        Image(TEST_IMAGE, width=40, height=15),
    )
    table.add_row("Different aspect ratios", sizings2_table)

    table_demo_table = Table("Name", "Birthday", "Picture")
    table_demo_table.add_row("Grace Hopper", "December 9, 1906", Image(TEST_IMAGE, width="auto", height="auto"))
    table.add_row("Images in tables", table_demo_table)

    table.add_row("... and in panels", Panel(Image(TEST_IMAGE, width=20, height="auto"), expand=False))

    Console().print(table)


if __name__ == "__main__":
    parser = ArgumentParser(description="Demo the capabilities of textual-kitty")
    parser.add_argument("-m", "--method", choices=[m.name for m in RenderingMethods], default="auto")
    arguments = parser.parse_args()
    run(RenderingMethods[arguments.method])
