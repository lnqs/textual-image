from unittest import skipUnless

from PIL import Image as PILImage
from PIL import ImageOps

from tests.data import BROKEN_IMAGE, TEST_IMAGE, TEXTUAL_ENABLED
from tests.utils import load_non_seekable_bytes_io


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_app() -> None:
    from textual.app import App, ComposeResult

    from textual_image.widget import Image

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
    async with app.run_test():
        with PILImage.open(TEST_IMAGE) as test_image:
            app.query_one(Image).image = ImageOps.flip(test_image)
        assert app.query_one(Image).image != TEST_IMAGE


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_unseekable_stream() -> None:
    from textual.app import App, ComposeResult

    from textual_image.widget import Image

    image = Image(load_non_seekable_bytes_io(TEST_IMAGE))

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield image
            yield image
            yield image

    app = TestApp()

    # Not testing too much reasonable stuff, but, well, at least the code gets executed
    async with app.run_test():
        with PILImage.open(TEST_IMAGE) as test_image:
            app.query_one(Image).image = ImageOps.flip(test_image)
        assert app.query_one(Image).image != TEST_IMAGE


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
def test_render_without_image() -> None:
    from textual_image.widget import Image

    assert Image().render() == ""


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_on_error_callback_in_image_setter() -> None:
    from textual.app import App, ComposeResult
    from textual.widgets import Static

    from textual_image.widget import Image

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield Image(
                TEST_IMAGE.read_bytes(), on_error=lambda e: Static(str(e))
            )  # in this case we should wrap it with BytesIO

    app = TestApp()

    async with app.run_test():
        widget = app.query_one(Image).children[0]
        assert isinstance(widget, Static)
        assert widget.content == "embedded null byte"


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_raise_without_on_error_in_image_setter() -> None:
    from textual.app import App, ComposeResult

    from textual_image.widget import Image

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield Image()

    app = TestApp()

    try:
        async with app.run_test():
            app.query_one(Image).image = TEST_IMAGE.read_bytes()
    except Exception:
        pass
    else:
        assert False


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_on_error_callback_in_render() -> None:
    from textual.app import App, ComposeResult
    from textual.widgets import Static

    from textual_image.widget import Image

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield Image(BROKEN_IMAGE, on_error=lambda e: Static(str(e)))

    app = TestApp()

    async with app.run_test():
        widget = app.query_one(Image).children[0]
        assert isinstance(widget, Static)
        assert widget.content == "image file is truncated"


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_raise_without_on_error_in_render() -> None:
    from textual.app import App, ComposeResult

    from textual_image.widget import Image

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield Image(BROKEN_IMAGE)

    app = TestApp()

    try:
        async with app.run_test():
            app.refresh(recompose=True)
    except Exception:
        pass
    else:
        assert False
