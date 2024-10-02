from textual_image._utils import clamp, grouped


def test_grouped() -> None:
    assert list(grouped([1, 2, 3, 4, 5, 6], 2)) == [(1, 2), (3, 4), (5, 6)]


def test_clamp() -> None:
    assert clamp(1, 50, 100) == 50
    assert clamp(150, 50, 100) == 100
    assert clamp(75, 50, 100) == 75
    assert clamp(50, 50, 100) == 50
    assert clamp(100, 50, 100) == 100
