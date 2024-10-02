#!/usr/bin/env python

"""Showcase textual-image's Textual Widgets."""

from argparse import ArgumentParser
from pathlib import Path
from typing import cast

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, HorizontalScroll, ScrollableContainer
from textual.css.scalar import Scalar
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label, OptionList, Select, TabbedContent, TabPane
from textual.widgets.option_list import Option

from textual_image.widget import HalfcellImage, SixelImage, TGPImage, UnicodeImage
from textual_image.widget import Image as AutoImage

TEST_IMAGE = Path(__file__).parent / ".." / "gracehopper.jpg"


RENDERING_METHODS = {
    "auto": AutoImage,
    "tgp": TGPImage,
    "sixel": SixelImage,
    "halfcell": HalfcellImage,
    "unicode": UnicodeImage,
}


class SizeGallery(Container):
    """Gallery im images with different sizing options set."""

    DEFAULT_CSS = """
    SizeGallery {
        layout: grid;
        grid-size: 3 2;

        Container {
            border: round gray;
            align: center middle;
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

    image_type: reactive[str | None] = reactive(None, recompose=True)

    def compose(self) -> ComposeResult:
        """Yields child widgets."""
        if not self.image_type:
            return

        Image = RENDERING_METHODS[self.image_type]

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


class SizingPlayground(Container):
    """Widget allowing to fiddle with image sizes."""

    DEFAULT_CSS = """
    SizingPlayground {
        border: round gray;
        align: center middle;

        ScrollableContainer {
            align: center middle;
        }

        Image {
            width: auto;
            height: 1fr;
        }

        Horizontal {
            height: auto;
            align: center middle;
        }

        Horizontal Label {
            padding-top: 1;
        }

        Horizontal Input {
            width: 10;
        }

        Horizontal Select {
            width: 13;
        }
    }
    """

    image_type: reactive[str | None] = reactive(None, recompose=True)

    def compose(self) -> ComposeResult:
        """Yields child widgets."""
        if not self.image_type:
            return

        Image = RENDERING_METHODS[self.image_type]

        with ScrollableContainer():
            yield Image(TEST_IMAGE)
        with Horizontal():
            units = ["cells", "%", "w", "h", "vw", "vh", "auto", "fr"]
            with Horizontal():
                yield Label("Width:")
                yield Input(type="integer", id="width-value", max_length=3)
                yield Select(
                    [(unit, unit) for unit in units], id="width-unit", prompt="unit", value="auto", allow_blank=False
                )
            with Horizontal():
                yield Label("Height:")
                yield Input(type="integer", id="height-value", max_length=3)
                yield Select(
                    [(unit, unit) for unit in units], id="height-unit", prompt="unit", value="auto", allow_blank=False
                )

    @on(Input.Changed)
    @on(Select.Changed)
    def size_changed(self, event: Input.Changed | Select.Changed) -> None:
        """Handles changes in size selectors."""
        assert self.image_type
        Image = RENDERING_METHODS[self.image_type]

        width_value = self.query_one("#width-value", Input).value
        width_unit = self.query_one("#width-unit", Select).value
        height_value = self.query_one("#height-value", Input).value
        height_unit = self.query_one("#height-unit", Select).value

        self.query_one("#width-value", Input).disabled = width_unit == "auto"
        self.query_one("#height-value", Input).disabled = height_unit == "auto"

        width_unit = "" if width_unit == "cells" else width_unit
        height_unit = "" if height_unit == "cells" else height_unit

        if (width_unit == "auto" or width_value != "") and (height_unit == "auto" or height_value != ""):
            width = f"{width_value if width_unit != 'auto' else ''}{width_unit}"
            height = f"{height_value if height_unit != 'auto' else ''}{height_unit}"

            image = self.query_one(Image)
            image.styles.width = Scalar.parse(width)
            image.styles.height = Scalar.parse(height)


class ManyGallery(Container):
    """Shows a changeable amount of images."""

    DEFAULT_CSS = """
    ManyGallery {
        border: round gray;

        HorizontalScroll {
            align: center middle;
            margin-bottom: 1;
        }

        HorizontalScroll Image {
            border: round gray;
            width: auto;
            height: 50%;
        }

        Horizontal {
            height: auto;
            align: center middle;
        }

        Label {
            padding: 1;
        }
    }
    """

    image_type: reactive[str | None] = reactive(None, recompose=True)
    image_count = reactive(8, recompose=True)

    def compose(self) -> ComposeResult:
        """Yields child widgets."""
        if not self.image_type:
            return
        Image = RENDERING_METHODS[self.image_type]

        with HorizontalScroll():
            for _ in range(self.image_count):
                yield Image(TEST_IMAGE)
        with Horizontal():
            with Horizontal():
                yield Button("-", id="remove-image", disabled=self.image_count == 0)
            yield Label(f"Images: {self.image_count}")
            with Horizontal():
                yield Button("+", id="add-image")

    @on(Button.Pressed, "#add-image")
    def add_image(self, event: Button.Pressed) -> None:
        """Adds one image to the gallery."""
        self.image_count += 1

    @on(Button.Pressed, "#remove-image")
    def remove_image(self, event: Button.Pressed) -> None:
        """Removes one image from the gallery."""
        self.image_count -= 1


class RenderingMethodSelectionScreen(ModalScreen[str]):
    """Modal to select the rendering method."""

    BINDINGS = [("escape", "app.pop_screen", "cancel")]

    DEFAULT_CSS = """
    RenderingMethodSelectionScreen {
        align: center middle;
    }

    RenderingMethodSelectionScreen > Container {
        width: auto;
        height: auto;
        background: $surface;
    }

    RenderingMethodSelectionScreen > Container > OptionList {
        width: 30;
        height: auto;
    }
    """

    def __init__(
        self,
        current_method: str,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initializes the rendering method selector."""
        super().__init__(name, id, classes)
        self.current_method = current_method

    def compose(self) -> ComposeResult:
        """Yields child widgets."""
        with Container():
            options = OptionList(*(Option(m, id=m) for m in RENDERING_METHODS.keys()))
            options.border_title = "Rendering method"
            options.highlighted = options.get_option_index(self.current_method)
            yield options

    @on(OptionList.OptionSelected)
    def set_rendering_method(self, event: OptionList.OptionSelected) -> None:
        """Dismisses the modal returning the selected rendering method."""
        self.dismiss(cast(str, event.option.prompt))


class DemoApp(App[None]):
    """App showcasing textual-image's image rendering capabilities."""

    BINDINGS = [("ctrl+r", "select_rendering_method", "rendering method")]

    CSS = """
    DemoApp {
    }
    """

    image_type: reactive[str | None] = reactive(None, recompose=True)

    def compose(self) -> ComposeResult:
        """Yields child widgets."""
        yield Header()
        with TabbedContent():
            with TabPane("Size Gallery", id="size-gallery"):
                yield SizeGallery().data_bind(DemoApp.image_type)
            with TabPane("Sizing Playground", id="sizing-playground"):
                yield SizingPlayground().data_bind(DemoApp.image_type)
            with TabPane("Many Images", id="many-images"):
                yield ManyGallery().data_bind(DemoApp.image_type)

        yield Footer()

    def action_select_rendering_method(self) -> None:
        """Shows a modal to select the rendering method."""
        assert self.image_type
        self.push_screen(RenderingMethodSelectionScreen(self.image_type), lambda m: self.set_rendering_method(m))

    def set_rendering_method(self, rendering_method: str) -> None:
        """Sets the rendering method.

        Args:
            rendering_method: Rendering method to use.
        """
        self.image_type = rendering_method


def run(rendering_method: str = "auto") -> None:
    """Showcase textual-image's Rich renderables."""
    app = DemoApp()
    app.image_type = rendering_method
    app.run()


if __name__ == "__main__":
    parser = ArgumentParser(description="Demo the capabilities of textual-image")
    parser.add_argument("-m", "--method", choices=RENDERING_METHODS.keys(), default="auto")
    arguments = parser.parse_args()
    run(arguments.method)
