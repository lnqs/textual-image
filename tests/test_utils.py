import io
from typing import Any

import pytest

from textual_image._utils import clamp, grouped, is_non_seekable_stream


def test_grouped() -> None:
    assert list(grouped([1, 2, 3, 4, 5, 6], 2)) == [(1, 2), (3, 4), (5, 6)]


def test_clamp() -> None:
    assert clamp(1, 50, 100) == 50
    assert clamp(150, 50, 100) == 100
    assert clamp(75, 50, 100) == 75
    assert clamp(50, 50, 100) == 50
    assert clamp(100, 50, 100) == 100


class UnseekableStream(io.BytesIO):
    def seekable(self) -> bool:
        return False


class SeekableStream(io.BytesIO):
    def seekable(self) -> bool:
        return True


class BrokenSeekableStream(io.BytesIO):
    def seekable(self) -> bool:
        raise RuntimeError("seekable not supported")


class NoSeekableAttribute:
    pass


@pytest.mark.parametrize(
    "stream, expected",
    [
        # seekable streams
        (io.BytesIO(), False),
        (io.StringIO(), False),
        (SeekableStream(), False),
        # non-seekable
        (UnseekableStream(), True),
        (BrokenSeekableStream(), False),
        # not a stream
        (NoSeekableAttribute(), False),
        (123, False),
        ("not a stream", False),
        (None, False),
    ],
)
def test_is_non_seekable_stream(stream: Any, expected: bool) -> None:
    assert is_non_seekable_stream(stream) == expected
