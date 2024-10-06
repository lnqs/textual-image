import io
from unittest.mock import patch

from rich.console import Console


def test_demo() -> None:
    from textual_image.demo.renderable import run

    stdout = io.StringIO()
    with patch.object(Console, "file", stdout):
        run("unicode")
    assert "textual-image's features" in stdout.getvalue()
