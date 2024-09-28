from pytest import raises

from tests.data import TERMINAL_SIZES
from textual_kitty.geometry import ImageSize


def test_image_size_validation() -> None:
    ImageSize(256, 256, None, None).validate()
    ImageSize(256, 256, 128, 128).validate()
    ImageSize(256, 256, "10%", "10%").validate()
    ImageSize(256, 256, "auto", "auto").validate()

    with raises(ValueError):
        ImageSize(256, 256, "-10%", "-10%").validate()

    with raises(ValueError):
        ImageSize(256, 256, "10", "10").validate()

    with raises(ValueError):
        ImageSize(256, 256, "xx%", "xx%").validate()


def test_image_size_cell_size_calculation() -> None:
    assert ImageSize(0, 0, None, None).get_cell_size(100, 100, TERMINAL_SIZES) == (0, 0)
    assert ImageSize(256, 256, None, None).get_cell_size(100, 100, TERMINAL_SIZES) == (32, 16)
    assert ImageSize(256, 256, "50%", "50%").get_cell_size(100, 100, TERMINAL_SIZES) == (50, 50)
    assert ImageSize(256, 256, "auto", "auto").get_cell_size(100, 100, TERMINAL_SIZES) == (100, 50)
    assert ImageSize(256, 256, "50%", "auto").get_cell_size(100, 100, TERMINAL_SIZES) == (50, 25)
    assert ImageSize(256, 256, 50, "auto").get_cell_size(100, 100, TERMINAL_SIZES) == (50, 25)
    assert ImageSize(256, 256, "auto", "50%").get_cell_size(100, 100, TERMINAL_SIZES) == (100, 50)
    assert ImageSize(256, 256, "auto", 50).get_cell_size(100, 100, TERMINAL_SIZES) == (100, 50)
    assert ImageSize(256, 256, "auto", None).get_cell_size(32, 32, TERMINAL_SIZES) == (32, 16)
    assert ImageSize(256, 256, None, "auto").get_cell_size(32, 32, TERMINAL_SIZES) == (32, 32)
    assert ImageSize(12, 512, "auto", "auto").get_cell_size(32, 32, TERMINAL_SIZES) == (2, 32)


def test_image_size_pixel_size_calculation() -> None:
    assert ImageSize(256, 256, None, None).get_pixel_size(100, 100, TERMINAL_SIZES) == (256, 256)
