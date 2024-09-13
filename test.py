#!/usr/bin/env python

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import cast

from PIL import Image as PILImage
from PIL import ImageOps

TEST_IMAGE = Path(__file__).parent / "gracehopper.jpg"


def demo_rich() -> None:
    from rich.console import Console
    from rich.style import Style
    from rich.table import Table

    from textual_kitty.rich import Image, TerminalError

    console = Console()

    console.print("KittyImage from path:", style=Style(bold=True))
    console.print(Image(TEST_IMAGE))

    console.print("\nKittyImage from pillow image:", style=Style(bold=True))
    with PILImage.open(TEST_IMAGE) as image:
        console.print(Image(image))

    console.print("\nSame KittyImage instance rendered twice:", style=Style(bold=True))
    image = Image(TEST_IMAGE)
    console.print(image)
    console.print(image)

    console.print("\nKittyImage with width set to 10:", style=Style(bold=True))
    console.print(Image(TEST_IMAGE, width=10))

    console.print("\nKittyImage inside table:", style=Style(bold=True))
    table = Table("Name", "Birthday", "Picture")
    table.add_row("Grace Hopper", "December 9, 1906", Image(TEST_IMAGE))
    console.print(table)

    console.print(
        "\nRaises exception if stdout is not connected to a terminal: ",
        style=Style(bold=True),
        end="",
    )
    try:
        capture_stream = io.StringIO()
        with redirect_stdout(capture_stream):
            console.print(Image(TEST_IMAGE))
    except TerminalError:
        console.print("OK", style=Style(bold=True, color="green"))
    else:
        console.print("Failed", style=Style(bold=True, color="red"))


def demo_textual() -> None:
    from textual import on
    from textual.app import App, ComposeResult
    from textual.containers import Container, HorizontalScroll, VerticalScroll
    from textual.widgets import Button, Collapsible, Footer, Header

    from textual_kitty.textual import Image

    class DemoApp(App[None]):
        DEFAULT_CSS = """
        DemoApp {
            #content {
                layout: grid;
                grid-size: 5 2;
            }

            #content > * {
                border: round gray;
                align: center middle;
            }

            .small {
                width: 6;
            }

            .full-row {
                column-span: 5;
            }

            .border {
                border: round white;
            }

            .width-auto {
                width: auto;
            }

            .width-full {
                width: 100%;
            }
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            with VerticalScroll(id="content"):
                with Container() as c:
                    c.border_title = "Grace from path"
                    yield Image(TEST_IMAGE)
                with Container() as c:
                    c.border_title = "Grace from PIL image"
                    with PILImage.open(TEST_IMAGE) as image:
                        yield Image(image)
                with Container() as c:
                    c.border_title = "Collapsible Grace"
                    with Collapsible(collapsed=False):
                        yield Image(TEST_IMAGE)
                with Container() as c:
                    c.border_title = "Small Grace"
                    yield Image(TEST_IMAGE, classes="small")
                with Container() as c:
                    c.border_title = "Flippable Grace"
                    with PILImage.open(TEST_IMAGE) as image:
                        yield Image(image, id="flippable")
                    yield Button("Flip", classes="width-full")
                with HorizontalScroll(classes="full-row") as c:
                    c.border_title = "Many Graces"
                    for _ in range(50):
                        yield Image(TEST_IMAGE, classes="border width-auto")
            yield Footer()

        @on(Button.Pressed)
        def button_pressed(self, _event: Button.Pressed) -> None:
            widget = self.query_one("#flippable", Image)
            widget.image = ImageOps.flip(cast(PILImage.Image, widget.image))

    DemoApp().run()


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("rich", "textual"):
        print(f"Usage: {sys.argv[0]} rich | textual", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == "rich":
        demo_rich()
    else:
        demo_textual()
