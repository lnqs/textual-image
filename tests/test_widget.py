from unittest.mock import MagicMock, Mock, patch

import pytest
from PIL import Image as PILImage
from PIL import ImageOps
from textual.app import App, ComposeResult

from tests.data import SIZE_ZERO, TERM_SIZE, TEST_IMAGE
from textual_kitty.widget import Image


async def test_app() -> None:
    class TestApp(App[None]):
        CSS = """
        .auto {
            width: auto;
            height: auto;
        }
        """

        def compose(self) -> ComposeResult:
            yield Image(TEST_IMAGE)
            yield Image(TEST_IMAGE, classes="auto")
            yield Image()
            yield Image(classes="auto")

    app = TestApp()

    # Not testing too much reasonable stuff, but, well, at least the code gets executed
    async with app.run_test():
        with PILImage.open(TEST_IMAGE) as test_image:
            app.query_one(Image).image = ImageOps.flip(test_image)
        assert app.query_one(Image).image != TEST_IMAGE


async def test_async_loading() -> None:
    image = Image()
    image._renderable = MagicMock(is_prepared=Mock(return_value=False))
    with patch.object(image, "_trigger_prepare_async") as trigger_prepare_async:
        image.render()
    assert not trigger_prepare_async.called

    image = Image(load_async=True)
    image._renderable = MagicMock(is_prepared=Mock(return_value=False))
    with patch.object(image, "_trigger_prepare_async") as trigger_prepare_async:
        image.render()
    assert trigger_prepare_async.called


@pytest.mark.filterwarnings("ignore:coroutine 'Widget._watch_loading' was never awaited")
async def test_trigger_prepare_async() -> None:
    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield Image(TEST_IMAGE, load_async=True)

    app = TestApp()

    async with app.run_test():
        image = app.query_one(Image)
        with patch.object(image._renderable, "prepare_async") as prepare_async:
            await image._trigger_prepare_async(SIZE_ZERO, TERM_SIZE).wait()
        assert prepare_async.called


def test_render_no_renderable() -> None:
    image = Image()

    with patch("textual_kitty.widget.get_terminal_size_info") as get_terminal_size_info:
        image.render()
    assert not get_terminal_size_info.called
