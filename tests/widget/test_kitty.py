from unittest import skipUnless
from unittest.mock import patch

from PIL import Image as PILImage
from PIL import ImageOps
from rich.console import Console
from rich.measure import Measurement

from tests.data import CONSOLE_OPTIONS, TEST_IMAGE, TEXTUAL_ENABLED


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_app() -> None:
    from textual.app import App, ComposeResult

    from textual_image.widget.kitty import Image

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

    with patch("textual_image.widget.kitty._send_tgp_message"):
        async with app.run_test() as pilot:
            with PILImage.open(TEST_IMAGE) as test_image:
                app.query_one(Image).image = ImageOps.flip(test_image)
            assert app.query_one(Image).image != TEST_IMAGE
            await pilot.pause()
            await pilot.app.run_action("app.command_palette")
            await pilot.pause()


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
def test_measure_noop_renderable() -> None:
    from textual_image.widget.kitty import _NoopRenderable

    assert _NoopRenderable(TEST_IMAGE).__rich_measure__(Console(), CONSOLE_OPTIONS) == Measurement(0, 0)


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
def test_on_unmount_cleanup() -> None:
    from textual_image.widget.kitty import _ImageKittyImpl

    with patch("textual_image.widget.kitty._send_tgp_message") as send_tgp_message:
        widget = _ImageKittyImpl()
        widget.on_unmount()

    assert send_tgp_message.call_args.kwargs["a"] == "d"
    assert send_tgp_message.call_args.kwargs["d"] == "I"
    assert send_tgp_message.call_args.kwargs["q"] == 2
