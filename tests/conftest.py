from typing import Iterator
from unittest.mock import patch

from pytest import fixture


# We mock stdin to be closed per default. The test code would get quite messy otherwise.
# Tests that need another value can just override it.
@fixture(scope="session", autouse=True)
def close_stdin() -> Iterator[None]:
    with patch("sys.__stdin__", None):
        yield


@fixture(scope="session", autouse=True)
def mock_cell_size() -> None:
    from textual_image._terminal import CellSize, get_cell_size

    setattr(get_cell_size, "_result", CellSize(10, 20))
