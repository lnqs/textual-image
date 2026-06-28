from unittest import skipUnless
from unittest.mock import PropertyMock, patch

from PIL import Image as PILImage
from PIL import ImageOps
from rich.console import Console
from rich.measure import Measurement
from rich.segment import Segment

from tests.data import CONSOLE_OPTIONS, TEST_IMAGE, TEXTUAL_ENABLED
from tests.utils import load_non_seekable_bytes_io


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
def test_cached_iterm2_data_is_hit() -> None:
    from textual.geometry import Region, Size

    from textual_image._terminal import CellSize
    from textual_image.widget.iterm2 import _CachedITerm2Data

    image = TEST_IMAGE
    crop = Region(0, 0, 10, 10)
    size = Size(10, 10)
    terminal_sizes = CellSize(10, 20)

    cached = _CachedITerm2Data(image, crop, size, terminal_sizes, "data")
    assert cached.is_hit(image, crop, size, terminal_sizes)
    assert not cached.is_hit(image, Region(1, 0, 10, 10), size, terminal_sizes)
    assert not cached.is_hit(image, crop, Size(5, 5), terminal_sizes)
    assert not cached.is_hit(image, crop, size, CellSize(8, 16))


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
def test_noop_renderable() -> None:
    from textual_image.widget.iterm2 import _NoopRenderable

    r = _NoopRenderable(TEST_IMAGE)
    assert r.__rich_measure__(Console(), CONSOLE_OPTIONS) == Measurement(0, 0)
    segments = list(r.__rich_console__(Console(), CONSOLE_OPTIONS))
    assert segments == [Segment("")]
    r.cleanup()


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_app() -> None:
    from textual.app import App, ComposeResult

    from textual_image.widget.iterm2 import Image

    class TestApp(App[None]):
        CSS = """
        .auto { width: auto; height: auto; }
        .fixed { width: 10; height: 10; }
        """

        def compose(self) -> ComposeResult:
            yield Image(TEST_IMAGE)
            yield Image(TEST_IMAGE, classes="auto")
            yield Image(TEST_IMAGE, classes="fixed")
            yield Image()

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

    app = TestApp()
    async with app.run_test() as pilot:
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
async def test_render_lines_no_image_returns_empty() -> None:
    from textual.app import App, ComposeResult
    from textual.geometry import Region

    from textual_image.widget.iterm2 import Image, _ImageITerm2Impl

    class TestApp(App[None]):
        def compose(self) -> ComposeResult:
            yield Image()

    async with TestApp().run_test() as pilot:
        impl = pilot.app.query_one(_ImageITerm2Impl)
        assert impl.render_lines(Region(0, 0, 10, 10)) == []


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_render_lines_uses_cache_on_second_call() -> None:
    from textual.app import App, ComposeResult
    from textual.geometry import Region

    from textual_image.widget.iterm2 import Image, _ImageITerm2Impl

    class TestApp(App[None]):
        CSS = "Image { width: 10; height: 10; }"

        def compose(self) -> ComposeResult:
            yield Image(TEST_IMAGE)

    async with TestApp().run_test() as pilot:
        await pilot.pause()
        impl = pilot.app.query_one(_ImageITerm2Impl)

        crop = Region(0, 0, impl.content_size.width, impl.content_size.height)
        impl.render_lines(crop)
        cached = impl._cached_iterm2_data

        impl.render_lines(crop)
        # ponytail: same object means cache was reused, not recomputed
        assert impl._cached_iterm2_data is cached


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_render_lines_clears_widget_area_before_iterm2() -> None:
    from textual.app import App, ComposeResult
    from textual.geometry import Region

    from textual_image.widget.iterm2 import Image, _ImageITerm2Impl

    class TestApp(App[None]):
        CSS = """
        Image { width: 4; height: 3; background: red; }
        """

        def compose(self) -> ComposeResult:
            yield Image(PILImage.new("RGBA", (2, 2), (0, 0, 0, 0)))

    async with TestApp().run_test() as pilot:
        await pilot.pause()
        impl = pilot.app.query_one(_ImageITerm2Impl)

        with patch.object(_ImageITerm2Impl, "_get_iterm2_segments", return_value=[Segment("ITERM2")]):
            lines = impl.render_lines(Region(0, 0, 4, 3))

        assert len(lines) == 3
        for strip in lines:
            clear_segment = strip._segments[0]
            assert clear_segment.text == " " * 4

        assert any(seg.text == "ITERM2" for seg in lines[-1]._segments)
