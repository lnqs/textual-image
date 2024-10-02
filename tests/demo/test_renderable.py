import io
from unittest.mock import patch

from rich.console import Console

from textual_kitty.demo.renderable import run


def test_demo() -> None:
    stdout = io.StringIO()
    with patch.object(Console, "file", stdout):
        run("unicode")
    assert "textual-kitty's features" in stdout.getvalue()
