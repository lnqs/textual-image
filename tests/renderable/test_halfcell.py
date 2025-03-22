from rich.console import Console
from rich.measure import Measurement
from syrupy.assertion import SnapshotAssertion

from tests.data import CONSOLE_OPTIONS, TEST_IMAGE
from tests.utils import load_non_seekable_bytes_io, render


def test_render(snapshot: SnapshotAssertion) -> None:
    from textual_image.renderable.halfcell import Image

    renderable = Image(TEST_IMAGE, width=4)
    assert render(renderable) == snapshot


def test_render_non_seekable() -> None:
    from textual_image.renderable.halfcell import Image

    test_image = load_non_seekable_bytes_io(TEST_IMAGE)
    renderable = Image(test_image)
    assert test_image.read() == b""
    assert render(renderable) == render(renderable)

    test_image.close()
    assert render(renderable) == render(renderable)


def test_measure() -> None:
    from textual_image.renderable.halfcell import Image

    renderable = Image(TEST_IMAGE, width=4)
    assert renderable.__rich_measure__(Console(), CONSOLE_OPTIONS) == Measurement(4, 4)


def test_cleanup() -> None:
    from textual_image.renderable.halfcell import Image

    # cleanup() is a no-op. Let's call it anyway.
    Image(TEST_IMAGE, width=4).cleanup()
