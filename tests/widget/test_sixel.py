from PIL import Image as PILImage
from PIL import ImageOps
from rich.console import Console
from rich.measure import Measurement
from textual.app import App, ComposeResult

from tests.data import CONSOLE_OPTIONS, TEST_IMAGE
from textual_kitty.widget.sixel import Image, _NoopRenderable


async def test_app() -> None:
    class TestApp(App[None]):
        CSS = """
        .auto {
            width: auto;
            height: auto;
        }
        .fixed {
            width: 10;
            height: 10;
        }
        """

        def compose(self) -> ComposeResult:
            yield Image(TEST_IMAGE)
            yield Image(TEST_IMAGE, classes="auto")
            yield Image(TEST_IMAGE, classes="fixed")
            yield Image()
            yield Image(classes="auto")

    app = TestApp()

    # Not testing too much reasonable stuff, but, well, at least the code gets executed
    async with app.run_test() as pilot:
        with PILImage.open(TEST_IMAGE) as test_image:
            app.query_one(Image).image = ImageOps.flip(test_image)
        assert app.query_one(Image).image != TEST_IMAGE
        await pilot.pause()
        await pilot.app.run_action("app.command_palette")
        await pilot.pause()


def test_measure_noop_renderable() -> None:
    assert _NoopRenderable(TEST_IMAGE).__rich_measure__(Console(), CONSOLE_OPTIONS) == Measurement(0, 0)
