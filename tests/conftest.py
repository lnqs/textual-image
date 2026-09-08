from typing import Iterator
from unittest.mock import patch

from pytest import fixture


# We mock stdin to be closed per default. The test code would get quite messy otherwise.
# Tests that need another value can just override it.
@fixture(scope="session", autouse=True)
def close_stdin() -> Iterator[None]:
    with patch("sys.__stdin__", None):
        yield


@fixture(autouse=True)
def mock_terminal_capabilities() -> None:
    from textual_image._terminal import CellSize, TerminalCapabilities, probe_terminal

    setattr(
        probe_terminal,
        "_result",
        TerminalCapabilities(CellSize(10, 20), sixel=False, tgp=False),
    )
