from unittest.mock import patch


def test_tmux_escape_wraps_and_escapes_terminal_sequence() -> None:
    from textual_image._tmux import tmux_escape

    seq = "\x1b_Gd=42\x1b\\"

    assert tmux_escape(seq) == "\x1bPtmux;\x1b\x1b_Gd=42\x1b\x1b\\\x1b\\"


def test_maybe_tmux_escape_uses_tmux_constant() -> None:
    from textual_image._tmux import maybe_tmux_escape, tmux_escape

    seq = "\x1b_Gd=42\x1b\\"

    with patch("textual_image._tmux.IS_TMUX", False):
        assert maybe_tmux_escape(seq) == seq

    with patch("textual_image._tmux.IS_TMUX", True):
        assert maybe_tmux_escape(seq) == tmux_escape(seq)
