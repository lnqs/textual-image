from unittest import skipIf, skipUnless
from unittest.mock import patch

from tests.data import TEXTUAL_ENABLED
from textual_image.__main__ import main


@skipUnless(TEXTUAL_ENABLED, "Textual support disabled")
def test_main() -> None:
    with patch("sys.argv", ["unittest", "rich"]):
        with patch("textual_image.demo.renderable.run") as run_rich:
            with patch("textual_image.demo.widget.run") as run_textual:
                main()
    assert run_rich.called
    assert not run_textual.called

    with patch("sys.argv", ["unittest", "textual"]):
        with patch("textual_image.demo.renderable.run") as run_rich:
            with patch("textual_image.demo.widget.run") as run_textual:
                main()
    assert not run_rich.called
    assert run_textual.called

    with patch("sys.argv", ["unittest", "textual"]):
        with patch("textual_image.demo.renderable.run") as run_rich:
            with patch("textual_image.demo.widget.run") as run_textual:
                with patch("textual_image.demo.cli.find_spec", return_value=None):
                    main()
    assert not run_rich.called
    assert not run_textual.called


@skipIf(TEXTUAL_ENABLED, "Textual support enabled")
def test_main_rich_only() -> None:
    with patch("sys.argv", ["unittest", "rich"]):
        with patch("textual_image.demo.renderable.run") as run_rich:
            main()
    assert run_rich.called

    with patch("sys.argv", ["unittest", "textual"]):
        with patch("textual_image.demo.renderable.run") as run_rich:
            with patch("sys.stderr") as stderr:
                main()
    assert stderr.write.called
    assert not run_rich.called
