import threading
from typing import cast
from unittest.mock import patch

from pytest import raises
from rich.console import Console
from rich.measure import Measurement

from tests.data import CONSOLE_OPTIONS, SIZE_ZERO, TERM_SIZE, TEST_IMAGE
from textual_kitty.geometry import Size
from textual_kitty.renderable._base import _Base


async def test_raises_on_unimplemented() -> None:
    renderable = _Base(TEST_IMAGE)

    with raises(NotImplementedError):
        renderable.is_prepared(SIZE_ZERO, TERM_SIZE)

    with raises(NotImplementedError):
        renderable.prepare(SIZE_ZERO, TERM_SIZE)

    with raises(NotImplementedError):
        await renderable.prepare_async(SIZE_ZERO, TERM_SIZE)

    with raises(NotImplementedError):
        renderable._render()

    # Just a no-op:
    renderable.cleanup()


def test_prepares_and_renders() -> None:
    renderable = _Base(TEST_IMAGE)

    with patch.object(renderable, "is_prepared", return_value=False):
        with patch.object(renderable, "prepare") as prepare:
            with patch.object(renderable, "_render") as render:
                list(renderable.__rich_console__(cast(Console, None), CONSOLE_OPTIONS))
    assert prepare.called
    assert render.called

    with patch.object(renderable, "is_prepared", return_value=True):
        with patch.object(renderable, "prepare") as prepare:
            with patch.object(renderable, "_render") as render:
                list(renderable.__rich_console__(cast(Console, None), CONSOLE_OPTIONS))
    assert not prepare.called
    assert render.called


def test_measures() -> None:
    renderable = _Base(TEST_IMAGE)

    with patch.object(renderable, "__rich_console__") as rich_console:
        measurement = renderable.__rich_measure__(cast(Console, None), CONSOLE_OPTIONS)
    assert measurement == Measurement(20, 20)
    assert not rich_console.called


def test_get_render_size() -> None:
    assert _Base(TEST_IMAGE).get_render_size(Size(50, 50), TERM_SIZE) == Size(50, 26)
    assert _Base(TEST_IMAGE, width=10).get_render_size(Size(50, 50), TERM_SIZE) == Size(10, 5)
    assert _Base(TEST_IMAGE, width=-1).get_render_size(Size(50, 50), TERM_SIZE) == Size(0, 0)
    assert _Base(TEST_IMAGE).get_render_size(Size(500, 50), TERM_SIZE) == Size(95, 50)


async def test_run_in_thread() -> None:
    renderable = _Base(TEST_IMAGE)
    result = await renderable._run_in_thread(lambda: threading.get_ident())
    assert result != threading.get_ident()
