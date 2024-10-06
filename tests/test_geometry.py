from pytest import raises

from tests.data import CELL_SIZE
from textual_image._geometry import ImageSize


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
    assert ImageSize(0, 0, None, None).get_cell_size(100, 100, CELL_SIZE) == (0, 0)
    assert ImageSize(256, 256, None, None).get_cell_size(100, 100, CELL_SIZE) == (26, 13)
    assert ImageSize(256, 256, "50%", "50%").get_cell_size(100, 100, CELL_SIZE) == (50, 50)
    assert ImageSize(256, 256, "auto", "auto").get_cell_size(100, 100, CELL_SIZE) == (100, 50)
    assert ImageSize(256, 256, "50%", "auto").get_cell_size(100, 100, CELL_SIZE) == (50, 25)
    assert ImageSize(256, 256, 50, "auto").get_cell_size(100, 100, CELL_SIZE) == (50, 25)
    assert ImageSize(256, 256, "auto", "50%").get_cell_size(100, 100, CELL_SIZE) == (100, 50)
    assert ImageSize(256, 256, "auto", 50).get_cell_size(100, 100, CELL_SIZE) == (100, 50)
    assert ImageSize(256, 256, "auto", None).get_cell_size(32, 32, CELL_SIZE) == (32, 13)
    assert ImageSize(256, 256, None, "auto").get_cell_size(32, 32, CELL_SIZE) == (26, 32)
    assert ImageSize(12, 512, "auto", "auto").get_cell_size(32, 32, CELL_SIZE) == (2, 32)


def test_image_size_pixel_size_calculation() -> None:
    assert ImageSize(256, 256, None, None).get_pixel_size(100, 100, CELL_SIZE) == (260, 260)
