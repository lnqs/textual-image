from PIL import Image as PILImage
from syrupy.assertion import SnapshotAssertion

from tests.data import TEST_IMAGE
from textual_image._sixel import image_to_sixels


def test_image_to_sixels(snapshot: SnapshotAssertion) -> None:
    with PILImage.open(TEST_IMAGE) as image:
        image = image.resize((16, 16))

    assert image_to_sixels(image) == snapshot
