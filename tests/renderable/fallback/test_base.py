from unittest.mock import patch

from PIL import Image as PILImage
from pytest import raises

from tests.data import SIZE_ZERO, TERM_SIZE, TEST_IMAGE
from textual_kitty.geometry import Size
from textual_kitty.renderable.fallback._base import _FallbackBase


async def test_raises_on_unimplemented() -> None:
    renderable = _FallbackBase(TEST_IMAGE)

    with raises(NotImplementedError):
        renderable._prepare_image(SIZE_ZERO, TERM_SIZE)

    with raises(NotImplementedError):
        renderable._calculate_image_size_for_render_size(SIZE_ZERO, TERM_SIZE)


def test_is_prepared() -> None:
    renderable = _FallbackBase(TEST_IMAGE)
    assert not renderable.is_prepared(SIZE_ZERO, TERM_SIZE)

    with patch.object(renderable, "_prepared_image", PILImage.new(mode="RGB", size=(10, 10))):
        with patch.object(renderable, "_calculate_image_size_for_render_size", return_value=Size(10, 10)):
            assert renderable.is_prepared(SIZE_ZERO, TERM_SIZE)


async def test_prepare() -> None:
    renderable = _FallbackBase(TEST_IMAGE)

    with patch.object(renderable, "_prepare_image") as _prepare_image:
        renderable.prepare(SIZE_ZERO, TERM_SIZE)
        assert _prepare_image.called

    with patch.object(renderable, "_prepare_image") as _prepare_image:
        await renderable.prepare_async(SIZE_ZERO, TERM_SIZE)
        assert _prepare_image.called
