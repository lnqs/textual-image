from importlib import import_module, reload
from unittest.mock import patch


def test_main() -> None:
    with patch("sys.argv", ["unittest", "rich"]):
        with patch("textual_kitty.demo.renderable.run") as run_rich:
            with patch("textual_kitty.demo.widget.run") as run_textual:
                main = import_module("textual_kitty.__main__")
    assert run_rich.called
    assert not run_textual.called

    with patch("sys.argv", ["unittest", "textual"]):
        with patch("textual_kitty.demo.renderable.run") as run_rich:
            with patch("textual_kitty.demo.widget.run") as run_textual:
                reload(main)
    assert not run_rich.called
    assert run_textual.called
