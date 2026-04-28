import os

IS_TMUX = bool(os.environ.get("TMUX"))


def maybe_tmux_escape(seq: str) -> str:
    """Escape a terminal sequence if we're running inside tmux."""
    if IS_TMUX:
        return tmux_escape(seq)

    return seq


_TMUX_ESCAPE_PREFIX = "\033Ptmux;"
_TMUX_ESCAPE_SUFFIX = "\033\\"
_TMUX_REPLACE = "\033"  # ESC


def tmux_escape(seq: str) -> str:
    """Wrap a terminal sequence in tmux's passthrough DCS envelope."""
    return _TMUX_ESCAPE_PREFIX + seq.replace(_TMUX_REPLACE, _TMUX_REPLACE * 2) + _TMUX_ESCAPE_SUFFIX
