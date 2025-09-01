from unittest import skipUnless
from unittest.mock import PropertyMock, patch

from PIL import Image as PILImage
from PIL import ImageOps
from rich.console import Console
from rich.measure import Measurement

from tests.data import CONSOLE_OPTIONS, TEST_IMAGE, TEXTUAL_ENABLED
from tests.utils import load_non_seekable_bytes_io


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_app() -> None:
    from textual.app import App, ComposeResult

    from textual_image.widget.sixel import Image

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


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_unseekable_stream() -> None:
    from textual.app import App, ComposeResult

    from textual_image.widget.sixel import Image

    image = Image(load_non_seekable_bytes_io(TEST_IMAGE))

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield image
            yield image
            yield image

    app = TestApp()

    # Not testing too much reasonable stuff, but, well, at least the code gets executed
    async with app.run_test() as pilot:
        with PILImage.open(TEST_IMAGE) as test_image:
            app.query_one(Image).image = ImageOps.flip(test_image)
        assert app.query_one(Image).image != TEST_IMAGE
        await pilot.pause()
        await pilot.app.run_action("app.command_palette")
        await pilot.pause()


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
def test_measure_noop_renderable() -> None:
    from textual_image.widget.sixel import _NoopRenderable

    assert _NoopRenderable(TEST_IMAGE).__rich_measure__(Console(), CONSOLE_OPTIONS) == Measurement(0, 0)


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_handling_no_screen_on_render() -> None:
    from textual.app import App, ComposeResult
    from textual.dom import NoScreen
    from textual.geometry import Region

    from textual_image.widget.sixel import Image, _ImageSixelImpl

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield Image(TEST_IMAGE)

    app = TestApp()

    async with app.run_test():
        sixel_impl = app.query_one(_ImageSixelImpl)

        result = sixel_impl.render_lines(Region(10, 10, 10, 10))
        assert result

        with patch.object(_ImageSixelImpl, "screen", PropertyMock(side_effect=NoScreen)):
            result = sixel_impl.render_lines(Region(10, 10, 10, 10))
            assert not result
