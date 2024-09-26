#!/usr/bin/env python

"""Showcase textual-kitty Renderables/Widgets."""

from argparse import ArgumentParser
from pathlib import Path
from typing import cast

from PIL import Image as PILImage

from textual_kitty.renderable import (
    HalfcellImage as HalfcellRenderable,
)
from textual_kitty.renderable import (
    Image as AutoRenderable,
)
from textual_kitty.renderable import (
    TGPImage as TGPRenderable,
)
from textual_kitty.renderable import (
    UnicodeImage as UnicodeRenderable,
)
from textual_kitty.widget import HalfcellImage as HalfcellWidget
from textual_kitty.widget import Image as AutoWidget
from textual_kitty.widget import TGPImage as TGPWidget
from textual_kitty.widget import UnicodeImage as UnicodeWidget

TEST_IMAGE = Path(__file__).parent / "gracehopper.jpg"

RENDERING_PROTOCOLS = {
    "auto": (AutoRenderable, AutoWidget),
    "tgp": (TGPRenderable, TGPWidget),
    "halfcell": (HalfcellRenderable, HalfcellWidget),
    "unicode": (UnicodeRenderable, UnicodeWidget),
}


def demo_rich(protocol: str) -> None:
    """Showcase textual-kitty's Rich renderables for images."""
    from rich.console import Console
    from rich.style import Style
    from rich.table import Table

    Image = RENDERING_PROTOCOLS[protocol][0]

    console = Console()

    console.print("Image, no size given:", style=Style(bold=True))
    console.print(Image(TEST_IMAGE))

    console.print("Image, 100% width:", style=Style(bold=True))
    console.print(Image(TEST_IMAGE, width="100%"))

    console.print("Image, 40 cells width, height auto:", style=Style(bold=True))
    console.print(Image(TEST_IMAGE, width=40, height="auto"))

    console.print("Image inside Table:", style=Style(bold=True))
    table = Table("Name", "Birthday", "Picture")
    table.add_row("Grace Hopper", "December 9, 1906", Image(TEST_IMAGE))
    console.print(table)


def demo_textual(protocol: str) -> None:
    """Showcase textual-kitty's Textual Widget for images."""
    from textual import on
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, HorizontalScroll, ScrollableContainer
    from textual.css.scalar import Scalar
    from textual.widgets import Button, Footer, Header, TabbedContent, TabPane

    Image = RENDERING_PROTOCOLS[protocol][1]

    class DemoApp(App[None]):
        CSS = """
        DemoApp {
            #sizing {
                layout: grid;
                grid-size: 3 2;
            }

            #sizing > * {
                border: round gray;
                align: center middle;
            }

            #zoom {
                border: round gray;
            }

            #zoom > * {
                align: center middle;
            }

            #zoom-in {
                margin-right: 1;
                width: 1fr;
            }

            #zoom-out {
                margin-left: 1;
                width: 1fr;
            }

            #many-container {
                align: center middle;
            }

            #many-container > Image {
                border: round gray;
            }

            .width-auto {
                width: auto;
            }

            .height-auto {
                height: auto;
            }

            .width-15 {
                width: 15;
            }

            .height-50pct {
                height: 50%;
            }

            .width-100pct {
                width: 100%;
            }
        }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            with TabbedContent():
                with TabPane("Sizing", id="sizing"):
                    with Container() as c:
                        c.border_title = "width: none; height: none;"
                        yield Image(TEST_IMAGE, classes="width-50-pc")
                    with Container() as c:
                        c.border_title = "width: auto; height: none;"
                        yield Image(TEST_IMAGE, classes="width-auto")
                    with Container() as c:
                        c.border_title = "width: none; height: auto;"
                        yield Image(TEST_IMAGE, classes="height-auto")
                    with Container() as c:
                        c.border_title = "width: auto; height: auto;"
                        yield Image(TEST_IMAGE, classes="width-auto height-auto")
                    with Container() as c:
                        c.border_title = "width: 15; height: auto;"
                        yield Image(TEST_IMAGE, classes="width-15 height-auto")
                    with Container() as c:
                        c.border_title = "width: auto; height: 50%;"
                        yield Image(TEST_IMAGE, classes="width-auto height-50pct")
                with TabPane("Zoom and Scroll", id="zoom"):
                    with ScrollableContainer():
                        yield Image(TEST_IMAGE, id="zoomable", classes="width-100pct height-auto")
                    with Horizontal(classes="height-auto"):
                        yield Button("+", id="zoom-in")
                        yield Button("-", id="zoom-out")
                with TabPane("Many Large Images", id="many"):
                    with PILImage.open(TEST_IMAGE) as large_image:
                        large_image = large_image.resize((large_image.width * 4, large_image.height * 4))
                    with HorizontalScroll(id="many-container"):
                        for _ in range(100):
                            yield Image(large_image, classes="width-auto height-50pct")
            yield Footer()

        @on(Button.Pressed, "#zoom-in")
        def zoom_in(self, event: Button.Pressed) -> None:
            widget = self.query_one("#zoomable", Image)
            widget.styles.width = int(cast(Scalar, widget.styles.width).value * 1.1)

        @on(Button.Pressed, "#zoom-out")
        def zoom_out(self, event: Button.Pressed) -> None:
            widget = self.query_one("#zoomable", Image)
            widget.styles.width = int(cast(Scalar, widget.styles.width).value / 1.1)

    DemoApp().run()


def run() -> None:
    """Run the textual_kitty demo."""
    parser = ArgumentParser(description="Demo the capabilities of textual-kitty")
    parser.add_argument("mode", choices=["rich", "textual"], nargs="?", default="rich")
    parser.add_argument("-p", "--protocol", choices=RENDERING_PROTOCOLS.keys(), default="auto")
    arguments = parser.parse_args()

    if arguments.mode == "rich":
        demo_rich(arguments.protocol)
    elif arguments.mode == "textual":
        demo_textual(arguments.protocol)


if __name__ == "__main__":
    run()
