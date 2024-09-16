import io
from typing import Any, AsyncContextManager, cast
from unittest.mock import patch

from rich.console import Console
from textual.app import App
from textual.pilot import Pilot
from textual.widgets import Button

from textual_kitty import demo
from textual_kitty.renderable.fallback.grayscale import Image


def test_arg_parsing() -> None:
    with patch("sys.argv", ["demo", "rich"]):
        with patch("textual_kitty.demo.demo_rich") as demo_rich:
            demo.run()
    assert demo_rich.called

    with patch("sys.argv", ["demo", "textual"]):
        with patch("textual_kitty.demo.demo_textual") as demo_textual:
            demo.run()
    assert demo_textual.called

    with patch("sys.argv", ["demo", "rich", "-p", "tgp"]):
        with patch("textual_kitty.demo.demo_rich") as demo_rich:
            demo.run()
    assert demo_rich.call_args[0][0].__module__ == "textual_kitty.renderable.tgp"

    with patch("sys.argv", ["demo", "rich", "-p", "colored-fallback"]):
        with patch("textual_kitty.demo.demo_rich") as demo_rich:
            demo.run()
    assert demo_rich.call_args[0][0].__module__ == "textual_kitty.renderable.fallback.colored"

    with patch("sys.argv", ["demo", "rich", "-p", "grayscale-fallback"]):
        with patch("textual_kitty.demo.demo_rich") as demo_rich:
            demo.run()
    assert demo_rich.call_args[0][0].__module__ == "textual_kitty.renderable.fallback.grayscale"


def test_rich() -> None:
    stdout = io.StringIO()
    with patch.object(Console, "file", stdout):
        demo.demo_rich(Image)
    assert "░░░░▒▒░░▒▒" in stdout.getvalue()


async def test_textual() -> None:
    # This is incredibly hacky. But is seems to work.
    awaitable = None

    def run_wrapper(app: App[Any]) -> None:
        nonlocal awaitable
        awaitable = app.run_test()

    # This doesn't actually test much, but at least we run the code.
    with patch.object(App, "run", run_wrapper):
        demo.demo_textual(Image)
        async with cast(AsyncContextManager[Pilot[Any]], awaitable) as pilot:
            pilot.app.query_one(Button).press()
            await pilot.pause()
