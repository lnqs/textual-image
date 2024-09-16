from unittest.mock import patch


def test_main() -> None:
    with patch("textual_kitty.demo.run") as run:
        import textual_kitty.__main__  # noqa: F401
    assert run.called
