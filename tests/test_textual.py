from array import array
from pathlib import Path
from typing import Any
from unittest.mock import patch

from PIL import Image as PILImage
from PIL import ImageOps
from textual.app import App, ComposeResult

from textual_kitty.textual import Image

TEST_IMAGE = Path(__file__).parent.parent / "gracehopper.jpg"


def mocked_ioctl(_fd: Any, _request: int, buf: array[int]) -> None:
    buf[0] = 58
    buf[1] = 120
    buf[2] = 960
    buf[3] = 1044


async def test_image() -> None:
    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield Image(TEST_IMAGE)

    with patch("textual_kitty.rich.ioctl", side_effect=mocked_ioctl):
        app = TestApp()
        async with app.run_test():
            image = app.query_one(Image)
            assert image._renderable and image._renderable._placement_size

            with PILImage.open(TEST_IMAGE) as test_image:
                app.query_one(Image).image = ImageOps.flip(test_image)
            assert app.query_one(Image).image != TEST_IMAGE


async def test_async_image() -> None:
    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield Image(TEST_IMAGE, load_async=True)

    with patch("textual_kitty.rich.ioctl", side_effect=mocked_ioctl):
        app = TestApp()
        async with app.run_test() as pilot:
            image = app.query_one(Image)
            assert image._renderable and not image._renderable._placement_size
            await pilot.pause()
            assert image._renderable and image._renderable._placement_size


async def test_image_auto_size() -> None:
    class TestApp(App[None]):
        CSS = """
        Image {
            width: auto;
            height: auto;
        }
        """

        def compose(self) -> ComposeResult:
            yield Image(TEST_IMAGE)

    with patch("textual_kitty.rich.ioctl", side_effect=mocked_ioctl):
        app = TestApp()
        async with app.run_test() as pilot:
            image = app.query_one(Image)
            assert image._renderable and image._renderable._placement_size
            app.query_one(Image).image = None
            await pilot.pause()
            assert not image._renderable
