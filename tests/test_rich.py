import io
from array import array
from pathlib import Path
from typing import Any
from unittest.mock import patch

from PIL import Image as PILImage
from pytest import raises
from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.table import Table
from syrupy.assertion import SnapshotAssertion

from textual_kitty.rich import (
    Image,
    TerminalError,
    TerminalSizeInformation,
    _send_terminal_graphics_protocol_message,
    get_terminal_size_info,
)

TEST_IMAGE = Path(__file__).parent.parent / "gracehopper.jpg"

MOCKED_TERM_SIZE_INFO = TerminalSizeInformation(
    rows=58,
    columns=120,
    screen_width=960,
    screen_height=1044,
    cell_width=8,
    cell_height=18,
)


def render(renderable: RenderableType, force_terminal: bool = True, height: int | None = None) -> str:
    mocked_stdout = io.StringIO()
    with patch(
        "textual_kitty.rich.get_terminal_size_info",
        return_value=MOCKED_TERM_SIZE_INFO,
    ):
        console = Console(
            width=MOCKED_TERM_SIZE_INFO.columns,
            height=MOCKED_TERM_SIZE_INFO.rows,
            file=mocked_stdout,
            color_system="truecolor",
            legacy_windows=False,
            force_terminal=force_terminal,
        )
        with patch("sys.__stdout__", mocked_stdout):
            console.print(renderable)
    return mocked_stdout.getvalue()


def test_from_file(snapshot: SnapshotAssertion) -> None:
    Image._next_image_id = 0xDEADBEEF
    assert render(Image(TEST_IMAGE)) == snapshot


def test_from_pillow_image(snapshot: SnapshotAssertion) -> None:
    Image._next_image_id = 0xDEADBEEF
    with PILImage.open(TEST_IMAGE) as image:
        assert render(Image(image)) == snapshot


def test_rendered_twice(snapshot: SnapshotAssertion) -> None:
    Image._next_image_id = 0xDEADBEEF
    image = Image(TEST_IMAGE)
    assert render(image) == snapshot
    with patch.object(image, "_prepare_terminal") as mocked_prepare_terminal:
        assert render(image) == snapshot
    assert not mocked_prepare_terminal.called


def test_explicit_width(snapshot: SnapshotAssertion) -> None:
    Image._next_image_id = 0xDEADBEEF
    assert render(Image(TEST_IMAGE, width=10)) == snapshot


def test_inside_table(snapshot: SnapshotAssertion) -> None:
    Image._next_image_id = 0xDEADBEEF
    table = Table("Name", "Birthday", "Picture")
    table.add_row("Grace Hopper", "December 9, 1906", Image(TEST_IMAGE))
    assert render(table) == snapshot


def test_missing_terminal_support() -> None:
    assert render(Image(TEST_IMAGE), force_terminal=False) == "[IMAGE]\n"


def test_inside_table_wo_terminal_support(snapshot: SnapshotAssertion) -> None:
    Image._next_image_id = 0xDEADBEEF
    table = Table("Name", "Birthday", "Picture")
    table.add_row("Grace Hopper", "December 9, 1906", Image(TEST_IMAGE))
    assert render(table, force_terminal=False) == snapshot


def test_negative_width() -> None:
    assert render(Image(TEST_IMAGE, width=-1)) == "\n"


def test_small_height(snapshot: SnapshotAssertion) -> None:
    assert render(Panel(Image(TEST_IMAGE), height=10)) == snapshot


def test_stdout_closed() -> None:
    with patch("sys.__stdout__", None):
        with raises(TerminalError):
            console = Console(
                width=MOCKED_TERM_SIZE_INFO.columns,
                height=MOCKED_TERM_SIZE_INFO.rows,
                file=io.StringIO(),
                color_system="truecolor",
                legacy_windows=False,
                force_terminal=True,
            )
            console.print(Image(TEST_IMAGE))

        with raises(TerminalError):
            _send_terminal_graphics_protocol_message()


def test_get_terminal_size_info() -> None:
    def mocked_ioctl(_fd: Any, _request: int, buf: array[int]) -> None:
        buf[0] = MOCKED_TERM_SIZE_INFO.rows
        buf[1] = MOCKED_TERM_SIZE_INFO.columns
        buf[2] = MOCKED_TERM_SIZE_INFO.screen_width
        buf[3] = MOCKED_TERM_SIZE_INFO.screen_height

    with patch("textual_kitty.rich.ioctl", side_effect=mocked_ioctl):
        assert get_terminal_size_info() == MOCKED_TERM_SIZE_INFO


def test_get_terminal_size_info_failing_ioctl() -> None:
    with patch("textual_kitty.rich.ioctl", side_effect=OSError()):
        with raises(TerminalError):
            get_terminal_size_info()


def test_get_terminal_size_zero_screen_size() -> None:
    def mocked_ioctl(_fd: Any, _request: int, buf: array[int]) -> None:
        buf[0] = MOCKED_TERM_SIZE_INFO.rows
        buf[1] = MOCKED_TERM_SIZE_INFO.columns
        buf[2] = 0
        buf[3] = 0

    with patch("textual_kitty.rich.ioctl", side_effect=mocked_ioctl):
        with raises(TerminalError):
            get_terminal_size_info()


def test_deleting_data_from_terminal() -> None:
    Image._next_image_id = 0xDEADBEEF
    image = Image(TEST_IMAGE)
    assert render(image) != ""

    with patch("sys.__stdout__", io.StringIO()) as mocked_stdout:
        image.delete_image_from_terminal()
    assert mocked_stdout.getvalue() == "\x1b_Ga=d,I=3735928559\x1b\\"
