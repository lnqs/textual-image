#!/usr/bin/env python

import io
from contextlib import redirect_stdout
from pathlib import Path

from PIL import Image

TEST_IMAGE = Path(__file__).parent / "gracehopper.jpg"


def demo_rich() -> None:
    from rich.console import Console
    from rich.style import Style
    from rich.table import Table

    from textual_kitty.rich import KittyError, KittyImage

    console = Console()

    console.print("KittyImage from path:", style=Style(bold=True))
    console.print(KittyImage(TEST_IMAGE))

    console.print("\nKittyImage from pillow image:", style=Style(bold=True))
    with Image.open(TEST_IMAGE) as image:
        console.print(KittyImage(image))

    console.print("\nSame KittyImage instance rendered twice:", style=Style(bold=True))
    image = KittyImage(TEST_IMAGE)
    console.print(image)
    console.print(image)

    console.print("\nKittyImage with width set to 10:", style=Style(bold=True))
    console.print(KittyImage(TEST_IMAGE, width=10))

    console.print("\nKittyImage inside table:", style=Style(bold=True))
    table = Table("Name", "Birthday", "Picture")
    table.add_row("Grace Hopper", "December 9, 1906", KittyImage(TEST_IMAGE))
    console.print(table)

    console.print(
        "\nRaises exception if stdout is not connected to a terminal: ",
        style=Style(bold=True),
        end="",
    )
    try:
        capture_stream = io.StringIO()
        with redirect_stdout(capture_stream):
            console.print(KittyImage(TEST_IMAGE))
    except KittyError:
        console.print("OK", style=Style(bold=True, color="green"))
    else:
        console.print("Failed", style=Style(bold=True, color="red"))


if __name__ == "__main__":
    demo_rich()
