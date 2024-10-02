from typing import Any, AsyncContextManager, cast
from unittest import skipUnless
from unittest.mock import patch

from tests.data import TEXTUAL_ENABLED


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
async def test_demo() -> None:
    from textual.app import App
    from textual.pilot import Pilot
    from textual.widgets import Input, Select, TabbedContent

    from textual_kitty.demo.widget import run

    # This is incredibly hacky. But is seems to work.
    awaitable = None

    def run_wrapper(app: App[Any]) -> None:
        nonlocal awaitable
        awaitable = app.run_test()

    # This doesn't actually test much, but at least we run the code.
    with patch.object(App, "run", run_wrapper):
        run("unicode")
        async with cast(AsyncContextManager[Pilot[Any]], awaitable) as pilot:
            # Switch to the sizing playground
            pilot.app.query_one(TabbedContent).active = "sizing-playground"
            await pilot.pause()
            pilot.app.query_one("#width-unit", Select).value = "%"
            pilot.app.query_one("#width-value", Input).value = "100"

            # Switch to the many images
            pilot.app.query_one(TabbedContent).active = "many-images"
            await pilot.pause()
            await pilot.click("#add-image")
            await pilot.click("#remove-image")

            # Open rendering method selector and select another method
            await pilot.press("ctrl+r")
            await pilot.pause()
            await pilot.press("up")
            await pilot.press("enter")
