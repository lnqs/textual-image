#!/usr/bin/env python

"""Showcase textual-kitty Renderables/Widgets."""

from argparse import ArgumentParser
from pathlib import Path
from typing import Type, cast

from PIL import Image as PILImage
from PIL import ImageOps

from textual_kitty.renderable._base import _Base

TEST_IMAGE = Path(__file__).parent / "gracehopper.jpg"


def demo_rich(Image: Type[_Base]) -> None:
    """Showcase textual-kitty's Rich Renderable for images."""
    from rich.console import Console
    from rich.style import Style
    from rich.table import Table

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


def demo_textual(Renderable: Type[_Base]) -> None:
    """Showcase textual-kitty's Textual Widget for images."""
    from textual import on
    from textual.app import App, ComposeResult
    from textual.containers import Container, HorizontalScroll, VerticalScroll
    from textual.widgets import Button, Collapsible, Footer, Header

    from textual_kitty.widget import Image

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
                    yield Image(TEST_IMAGE, image_renderable_type=Renderable)
                with Container() as c:
                    c.border_title = "Grace from PIL image"
                    with PILImage.open(TEST_IMAGE) as image:
                        yield Image(image, image_renderable_type=Renderable)
                with Container() as c:
                    c.border_title = "Collapsible Grace"
                    with Collapsible(collapsed=False):
                        yield Image(TEST_IMAGE, image_renderable_type=Renderable)
                with Container() as c:
                    c.border_title = "Small Grace"
                    yield Image(TEST_IMAGE, image_renderable_type=Renderable, classes="small")
                with Container() as c:
                    c.border_title = "Flippable Grace"
                    with PILImage.open(TEST_IMAGE) as image:
                        yield Image(image, image_renderable_type=Renderable, id="flippable")
                    yield Button("Flip", classes="width-full")
                with HorizontalScroll(classes="full-row") as c:
                    c.border_title = "Many Graces (huge, loaded async)"
                    with PILImage.open(TEST_IMAGE) as image:
                        image = image.resize((image.width * 4, image.height * 4))
                    for _ in range(50):
                        yield Image(
                            image, image_renderable_type=Renderable, classes="border width-auto", load_async=True
                        )
            yield Footer()

        @on(Button.Pressed)
        def button_pressed(self, _event: Button.Pressed) -> None:
            widget = self.query_one("#flippable", Image)
            widget.image = ImageOps.flip(cast(PILImage.Image, widget.image))

    DemoApp().run()


def run() -> None:
    """Run the textual_kitty demo."""
    parser = ArgumentParser(description="Demo the capabilities of textual-kitty")
    parser.add_argument("mode", choices=["rich", "textual"], nargs="?", default="rich")
    parser.add_argument(
        "-p", "--protocol", choices=["auto", "tgp", "colored-fallback", "grayscale-fallback"], default="auto"
    )
    arguments = parser.parse_args()

    if arguments.protocol == "auto":
        from textual_kitty.renderable import Image
    elif arguments.protocol == "tgp":
        from textual_kitty.renderable.tgp import Image
    elif arguments.protocol == "colored-fallback":
        from textual_kitty.renderable.fallback.colored import Image
    elif arguments.protocol == "grayscale-fallback":
        from textual_kitty.renderable.fallback.grayscale import Image

    if arguments.mode == "rich":
        demo_rich(Image)
    elif arguments.mode == "textual":
        demo_textual(Image)


if __name__ == "__main__":
    run()
