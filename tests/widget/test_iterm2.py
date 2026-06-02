from unittest import skipUnless
from unittest.mock import PropertyMock, patch

from PIL import Image as PILImage
from PIL import ImageOps

from tests.data import TEST_IMAGE, TEXTUAL_ENABLED
from tests.utils import load_non_seekable_bytes_io


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
def test_noop_renderable_console() -> None:
    from rich.console import Console

    from tests.data import CONSOLE_OPTIONS
    from textual_image.widget.iterm2 import _NoopRenderable

    renderable = _NoopRenderable(TEST_IMAGE)
    segments = list(renderable.__rich_console__(Console(), CONSOLE_OPTIONS))
    assert len(segments) == 1
    assert segments[0].text == ""


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
def test_noop_renderable_measure() -> None:
    from rich.console import Console
    from rich.measure import Measurement

    from tests.data import CONSOLE_OPTIONS
    from textual_image.widget.iterm2 import _NoopRenderable

    assert _NoopRenderable(TEST_IMAGE).__rich_measure__(Console(), CONSOLE_OPTIONS) == Measurement(0, 0)


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
def test_noop_renderable_cleanup() -> None:
    from textual_image.widget.iterm2 import _NoopRenderable

    _NoopRenderable(TEST_IMAGE).cleanup()


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
def test_cached_iterm2_data_hit() -> None:
    from textual.geometry import Region, Size

    from textual_image._terminal import CellSize
    from textual_image.widget.iterm2 import _CachedITerm2Data

    cell_size = CellSize(10, 20)
    crop = Region(0, 0, 4, 4)
    content_size = Size(4, 4)
    cached = _CachedITerm2Data(TEST_IMAGE, crop, content_size, cell_size, "data")

    assert cached.is_hit(TEST_IMAGE, crop, content_size, cell_size)


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
def test_cached_iterm2_data_miss_image() -> None:
    from textual.geometry import Region, Size

    from textual_image._terminal import CellSize
    from textual_image.widget.iterm2 import _CachedITerm2Data

    cell_size = CellSize(10, 20)
    crop = Region(0, 0, 4, 4)
    content_size = Size(4, 4)
    cached = _CachedITerm2Data(TEST_IMAGE, crop, content_size, cell_size, "data")

    other_image = PILImage.new("RGB", (2, 2))
    assert not cached.is_hit(other_image, crop, content_size, cell_size)


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
def test_cached_iterm2_data_miss_crop() -> None:
    from textual.geometry import Region, Size

    from textual_image._terminal import CellSize
    from textual_image.widget.iterm2 import _CachedITerm2Data

    cell_size = CellSize(10, 20)
    crop = Region(0, 0, 4, 4)
    content_size = Size(4, 4)
    cached = _CachedITerm2Data(TEST_IMAGE, crop, content_size, cell_size, "data")

    assert not cached.is_hit(TEST_IMAGE, Region(1, 0, 4, 4), content_size, cell_size)


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
def test_cached_iterm2_data_miss_content_size() -> None:
    from textual.geometry import Region, Size

    from textual_image._terminal import CellSize
    from textual_image.widget.iterm2 import _CachedITerm2Data

    cell_size = CellSize(10, 20)
    crop = Region(0, 0, 4, 4)
    content_size = Size(4, 4)
    cached = _CachedITerm2Data(TEST_IMAGE, crop, content_size, cell_size, "data")

    assert not cached.is_hit(TEST_IMAGE, crop, Size(8, 8), cell_size)


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
def test_cached_iterm2_data_miss_terminal_sizes() -> None:
    from textual.geometry import Region, Size

    from textual_image._terminal import CellSize
    from textual_image.widget.iterm2 import _CachedITerm2Data

    cell_size = CellSize(10, 20)
    crop = Region(0, 0, 4, 4)
    content_size = Size(4, 4)
    cached = _CachedITerm2Data(TEST_IMAGE, crop, content_size, cell_size, "data")

    assert not cached.is_hit(TEST_IMAGE, crop, content_size, CellSize(8, 16))


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_app() -> None:
    from textual.app import App, ComposeResult

    from textual_image.widget.iterm2 import Image

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

    async with app.run_test() as pilot:
        with PILImage.open(TEST_IMAGE) as test_image:
            app.query_one(Image).image = ImageOps.flip(test_image)
        assert app.query_one(Image).image != TEST_IMAGE
        await pilot.pause()


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_unseekable_stream() -> None:
    from textual.app import App, ComposeResult

    from textual_image.widget.iterm2 import Image

    image = Image(load_non_seekable_bytes_io(TEST_IMAGE))

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield image
            yield image
            yield image

    app = TestApp()

    async with app.run_test() as pilot:
        with PILImage.open(TEST_IMAGE) as test_image:
            app.query_one(Image).image = ImageOps.flip(test_image)
        assert app.query_one(Image).image != TEST_IMAGE
        await pilot.pause()


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_handling_no_screen_on_render() -> None:
    from textual.app import App, ComposeResult
    from textual.dom import NoScreen
    from textual.geometry import Region

    from textual_image.widget.iterm2 import Image, _ImageITerm2Impl

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield Image(TEST_IMAGE)

    app = TestApp()

    async with app.run_test():
        impl = app.query_one(_ImageITerm2Impl)

        result = impl.render_lines(Region(0, 0, 10, 10))
        assert result

        with patch.object(_ImageITerm2Impl, "screen", PropertyMock(side_effect=NoScreen)):
            result = impl.render_lines(Region(0, 0, 10, 10))
            assert not result


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_render_lines_no_image() -> None:
    from textual.app import App, ComposeResult
    from textual.geometry import Region

    from textual_image.widget.iterm2 import Image, _ImageITerm2Impl

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield Image()

    app = TestApp()

    async with app.run_test():
        impl = app.query_one(_ImageITerm2Impl)
        result = impl.render_lines(Region(0, 0, 10, 10))
        assert not result


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_render_lines_clears_widget_area_before_iterm2() -> None:
    from textual.app import App, ComposeResult
    from textual.geometry import Region

    from textual_image.widget.iterm2 import Image, _ImageITerm2Impl

    class TestApp(App[None]):
        CSS = """
        Image {
            width: 4;
            height: 3;
            background: red;
        }
        """

        def compose(self) -> ComposeResult:
            yield Image(PILImage.new("RGBA", (2, 2), (0, 0, 0, 0)))

    app = TestApp()

    async with app.run_test():
        impl = app.query_one(_ImageITerm2Impl)
        lines = impl.render_lines(Region(0, 0, 4, 3))

        assert len(lines) == 3

        for strip in lines:
            clear_segment = strip._segments[0]
            assert clear_segment.text == " " * 4
            assert str(clear_segment.style) == "on #ff0000"


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_render_lines_caches_iterm2_data() -> None:
    from textual.app import App, ComposeResult
    from textual.geometry import Region

    from textual_image.widget.iterm2 import Image, _ImageITerm2Impl

    class TestApp(App[None]):
        CSS = """
        Image {
            width: 4;
            height: 3;
        }
        """

        def compose(self) -> ComposeResult:
            yield Image(TEST_IMAGE)

    app = TestApp()

    async with app.run_test():
        impl = app.query_one(_ImageITerm2Impl)
        crop = Region(0, 0, 4, 3)

        impl.render_lines(crop)
        assert impl._cached_iterm2_data is not None
        cached_data = impl._cached_iterm2_data.iterm2_data

        impl.render_lines(crop)
        assert impl._cached_iterm2_data.iterm2_data is cached_data


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_image_setter_triggers_recompose() -> None:
    from textual.app import App, ComposeResult

    from textual_image.widget.iterm2 import Image

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield Image(TEST_IMAGE)

    app = TestApp()

    async with app.run_test():
        img_widget = app.query_one(Image)
        with patch.object(img_widget, "refresh") as mock_refresh:
            img_widget.image = PILImage.new("RGB", (1, 1))
        mock_refresh.assert_called_once_with(recompose=True)
