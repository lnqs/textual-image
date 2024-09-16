from typing import cast

from PIL import Image as PILImage
from rich.color import Color
from syrupy.assertion import SnapshotAssertion

from tests.data import SIZE_TEN, TERM_SIZE, TEST_IMAGE
from tests.util import render
from textual_kitty.renderable.fallback.colored import Image


def test_prepare() -> None:
    renderable = Image(TEST_IMAGE)
    renderable.prepare(SIZE_TEN, TERM_SIZE)
    assert cast(PILImage.Image, renderable._prepared_image).size == (10, 22)


async def test_prepare_async() -> None:
    renderable = Image(TEST_IMAGE)
    await renderable.prepare_async(SIZE_TEN, TERM_SIZE)
    assert cast(PILImage.Image, renderable._prepared_image).size == (10, 22)


def test_calculate_image_size_for_render_size() -> None:
    renderable = Image(TEST_IMAGE)
    assert renderable._calculate_image_size_for_render_size(SIZE_TEN, TERM_SIZE) == (10, 22)


def test_render_not_prepared() -> None:
    renderable = Image(TEST_IMAGE)
    assert list(renderable._render()) == []


def test_render(snapshot: SnapshotAssertion) -> None:
    renderable = Image(TEST_IMAGE, width=4)
    assert render(renderable) == snapshot


def test_get_pixel_failure() -> None:
    renderable = Image(TEST_IMAGE)
    assert renderable._get_pixel(0, 0) == Color.default()
