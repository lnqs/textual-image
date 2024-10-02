from base64 import b64decode

from PIL import Image as PILImage

from tests.data import TEST_IMAGE
from textual_image._pixeldata import PixelData, PixelMeta, ensure_image


def test_ensure_image() -> None:
    with ensure_image(TEST_IMAGE) as image:
        assert isinstance(image, PILImage.Image)

    with PILImage.open(TEST_IMAGE) as opened_image:
        with ensure_image(opened_image) as image:
            assert isinstance(image, PILImage.Image)
            assert image is opened_image


def test_pixel_meta() -> None:
    with PILImage.open(TEST_IMAGE) as image:
        meta = PixelMeta(image)
        assert meta.width == image.width
        assert meta.height == image.height


def test_pixel_data_mode() -> None:
    with PILImage.open(TEST_IMAGE) as image:
        assert PixelData(image, mode="grayscale")._image.mode == "L"
        assert PixelData(image, mode="rgb")._image.mode == "RGB"


def test_pixel_data_size() -> None:
    with PILImage.open(TEST_IMAGE) as image:
        data = PixelData(image)
        assert data.width == image.width
        assert data.height == image.height


def test_pixel_data_pil_image() -> None:
    data = PixelData(TEST_IMAGE)
    assert isinstance(data.pil_image, PILImage.Image)


def test_pixel_data_scale() -> None:
    data = PixelData(TEST_IMAGE).scaled(32, 32)
    assert data._image.width == 32
    assert data._image.height == 32


def test_pixel_data_crop() -> None:
    data = PixelData(TEST_IMAGE).cropped(32, 32, 64, 64)
    assert data._image.width == 32
    assert data._image.height == 32


def test_pixel_data_to_base64() -> None:
    data = PixelData(TEST_IMAGE).to_base64()
    b64decode(data)  # must not raise


def test_pixel_data_iteration() -> None:
    data = PixelData(TEST_IMAGE).scaled(8, 8)
    assert len(list(data)) == 8
    assert all(len(list(row)) == 8 for row in data)
