from unittest.mock import patch

import pytest
from PIL import Image as PILImage
from syrupy.assertion import SnapshotAssertion

from tests.data import TEST_IMAGE
from textual_image._sixel import (
    SixelOptions,
    _compact_palette,
    _iter_bands,
    image_to_sixels,
)


def test_image_to_sixels(snapshot: SnapshotAssertion) -> None:
    with PILImage.open(TEST_IMAGE) as image:
        scaled_image = image.resize((16, 16))

    assert image_to_sixels(scaled_image) == snapshot


def test_default_quantize_matches_fastoctree_and_is_smaller_than_adaptive() -> None:
    """The default quantizer should stay on the compact fastoctree path."""
    with PILImage.open(TEST_IMAGE) as opened_image:
        image = opened_image.resize((16, 16))

    default_result = image_to_sixels(image)
    fastoctree_result = image_to_sixels(image, SixelOptions(quantize="fastoctree"))
    adaptive_result = image_to_sixels(image, SixelOptions(quantize="adaptive"))

    assert default_result == fastoctree_result
    assert len(default_result) < len(adaptive_result)


def test_maxcoverage_smaller_than_fastoctree_for_large_images() -> None:
    """maxcoverage produces smaller output for images >= 64x64."""
    with PILImage.open(TEST_IMAGE) as opened_image:
        image = opened_image.resize((128, 128))

    fastoctree = image_to_sixels(image, SixelOptions(quantize="fastoctree"))
    maxcoverage = image_to_sixels(image, SixelOptions(quantize="maxcoverage"))

    assert len(maxcoverage) < len(fastoctree)


def test_paletted_input_skips_requantize() -> None:
    """Already-paletted inputs within budget should bypass Pillow quantization."""
    image = PILImage.new("P", (4, 1))
    palette = [0, 0, 0] * 256
    palette[0:3] = [255, 0, 0]
    palette[3:6] = [0, 0, 255]
    image.putpalette(palette)
    image.putdata([0, 1, 0, 1])

    with patch("textual_image._sixel._quantize_rgb_image", side_effect=AssertionError("unexpected requantize")):
        image_to_sixels(image)


def test_grayscale_input_skips_requantize() -> None:
    """Grayscale inputs within budget should be converted to P directly."""
    image = PILImage.new("L", (4, 1))
    image.putdata([0, 64, 128, 255])

    with patch("textual_image._sixel._quantize_rgb_image", side_effect=AssertionError("unexpected requantize")):
        image_to_sixels(image)


def test_reuses_active_palette_tag_across_bands() -> None:
    """A single-color multi-band image should not repeat the same body tag."""
    image = PILImage.new("RGB", (4, 8), color=(255, 0, 0))

    result = image_to_sixels(image)

    # #0 appears once: the definition #0;2;R;G;B in band 1.
    # Band 2 reuses the still-active color, so no second #0 is emitted.
    assert result.count("#0") == 1


def test_reuses_color_across_band_transition() -> None:
    """A shared color should stay active into the next band when possible."""
    image = PILImage.new("P", (4, 12))
    palette = [0, 0, 0] * 256
    palette[0:3] = [255, 0, 0]
    palette[3:6] = [0, 255, 0]
    palette[6:9] = [0, 0, 255]
    image.putpalette(palette)

    pixels = [0] * (image.width * image.height)
    for y in range(6):
        pixels[y * image.width] = 1
    for y in range(6, 12):
        pixels[y * image.width + 1] = 2
    image.putdata(pixels)

    result = image_to_sixels(image)

    # 3 color definitions total; each defined once on first use.
    # Interleaved packing means non-overlapping colors share a pass,
    # and the active color carries across band transitions.
    assert result.count("#") == 3
    assert result.count("#0") == 1


def test_image_to_sixels_smooth() -> None:
    """Test that smooth option applies ModeFilter."""
    with PILImage.open(TEST_IMAGE) as opened_image:
        image = opened_image.resize((16, 16))

    result_no_smooth = image_to_sixels(image)
    result_smooth = image_to_sixels(image, SixelOptions(smooth=5))
    # Smooth produces different (typically smaller) output
    assert result_smooth != result_no_smooth


def test_image_to_sixels_non_rgb() -> None:
    """Test that non-RGB images are converted before encoding."""
    with PILImage.open(TEST_IMAGE) as opened_image:
        image = opened_image.resize((8, 8))

    rgba_image = image.convert("RGBA")
    rgb_result = image_to_sixels(image)
    rgba_result = image_to_sixels(rgba_image)
    assert rgb_result == rgba_result


def test_image_to_sixels_numpy_path() -> None:
    """Test the numpy-based encoding path."""
    pytest.importorskip("numpy")

    with PILImage.open(TEST_IMAGE) as opened_image:
        image = opened_image.resize((16, 16))

    # Get result via pure-Python path
    with patch("textual_image._sixel._HAS_NUMPY", False):
        expected = image_to_sixels(image)

    # Get result via numpy path
    with patch("textual_image._sixel._HAS_NUMPY", True):
        result = image_to_sixels(image)

    assert result == expected


def test_iter_bands_numpy_matches_pure_python() -> None:
    """NumPy and pure-Python band iteration produce identical output."""
    pytest.importorskip("numpy")

    with PILImage.open(TEST_IMAGE) as opened_image:
        image = opened_image.resize((16, 16))

    quantized = image.quantize(colors=256, method=PILImage.Quantize.MAXCOVERAGE)
    raw_data = quantized.tobytes()
    data, registers = _compact_palette(quantized, raw_data)

    from textual_image._sixel import _iter_bands_np

    py_out = b"".join(_iter_bands(data, quantized.width, quantized.height, registers))
    np_out = b"".join(_iter_bands_np(data, quantized.width, quantized.height, registers))

    assert np_out == py_out


def test_iter_bands_single_color() -> None:
    """Single-color images encode correctly regardless of acceleration path."""
    pytest.importorskip("numpy")

    image = PILImage.new("RGB", (4, 8), color=(255, 0, 0))
    quantized = image.quantize(colors=256, method=PILImage.Quantize.MAXCOVERAGE)
    raw_data = quantized.tobytes()
    data, registers = _compact_palette(quantized, raw_data)

    from textual_image._sixel import _iter_bands_np

    py_out = b"".join(_iter_bands(data, quantized.width, quantized.height, registers))
    np_out = b"".join(_iter_bands_np(data, quantized.width, quantized.height, registers))

    assert np_out == py_out


def test_compact_palette_reindexes_sparse_colors() -> None:
    """Used colors should be remapped into a dense register range."""
    image = PILImage.new("P", (3, 1))
    palette = [0, 0, 0] * 256
    palette[200 * 3 : 200 * 3 + 3] = [255, 0, 0]
    palette[250 * 3 : 250 * 3 + 3] = [0, 0, 255]
    image.putpalette(palette)

    remapped, color_registers = _compact_palette(image, bytes([250, 200, 250]))

    assert remapped == bytes([0, 1, 0])
    assert color_registers == (b"#0;2;0;0;100", b"#1;2;100;0;0")


def test_compact_palette_deduplicates_identical_sixel_colors() -> None:
    """Palette entries that collapse to the same sixel RGB should share a register."""
    image = PILImage.new("P", (4, 1))
    palette = [0, 0, 0] * 256
    palette[10 * 3 : 10 * 3 + 3] = [254, 0, 0]
    palette[200 * 3 : 200 * 3 + 3] = [255, 0, 0]
    image.putpalette(palette)

    remapped, color_registers = _compact_palette(image, bytes([10, 200, 10, 200]))

    assert remapped == bytes([0, 0, 0, 0])
    assert color_registers == (b"#0;2;100;0;0",)
