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
def test_image_to_sixels_inside_tmux_uses_native_sixel() -> None:
    from textual_image.widget.sixel import _ImageSixelImpl

    image = PILImage.new("RGB", (1, 1), (255, 0, 0))
    sixel_impl = _ImageSixelImpl()

    with patch("textual_image._tmux.IS_TMUX", True):
        sixel_data = sixel_impl._image_to_sixels(image)

    assert sixel_data.startswith("\x1bP0;0;0q")
    assert "\x1bPtmux;" not in sixel_data


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


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
def test_default_options_subclass_override() -> None:
    """Subclasses can override ``DEFAULT_OPTIONS`` to change the encoding default."""
    from textual_image._sixel import SixelOptions
    from textual_image.widget.sixel import Image, _NoopRenderable

    class LazyImage(Image, Renderable=_NoopRenderable):
        DEFAULT_OPTIONS = SixelOptions(lazy_color_palette=True)

    # Without an override, ``_sixel_options`` is left as ``None`` so
    # ``image_to_sixels`` applies its own default.
    assert Image(TEST_IMAGE)._sixel_options is None
    assert LazyImage(TEST_IMAGE)._sixel_options == SixelOptions(lazy_color_palette=True)

    explicit = SixelOptions(colors=64)
    assert Image(TEST_IMAGE, sixel_options=explicit)._sixel_options is explicit


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_render_lines_clears_widget_area_before_sixel() -> None:
    from textual.app import App, ComposeResult
    from textual.geometry import Region

    from textual_image.widget.sixel import Image, _ImageSixelImpl

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
        sixel_impl = app.query_one(_ImageSixelImpl)

        with patch.object(_ImageSixelImpl, "_get_sixel_segments", return_value=[Segment("SIXEL")]):
            lines = sixel_impl.render_lines(Region(0, 0, 4, 3))

        assert len(lines) == 3

        for strip in lines:
            clear_segment = strip._segments[0]
            assert clear_segment.text == " " * 4
            assert str(clear_segment.style) == "on #ff0000"

        assert any(segment.text == "SIXEL" for segment in lines[-1]._segments)
