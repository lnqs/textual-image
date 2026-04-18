from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Literal, TypeAlias

from PIL import Image as PILImage
from PIL import ImageFilter

try:
    import numpy as np

    _HAS_NUMPY = True
except ImportError:  # pragma: no cover
    _HAS_NUMPY = False

MAX_COLORS = 256

# Sixel protocol bytes
_SIXEL_OFFSET = 0x3F  # ASCII '?', added to 0-63 sixel values to make them printable
_CR = 0x24  # '$' carriage return
_NL = 0x2D  # '-' newline
_ST = b"\x1b\\"  # String Terminator

_BAND_HEIGHT = 6  # Rows per sixel band
_RLE_THRESHOLD = 4  # Runs shorter than this are emitted raw
_GAP_THRESHOLD = 10  # Split spans with internal gaps >= this many empty columns

# RGB 0-255 -> sixel percentage 0-100 (rounded)
_RGB_TO_PCT = tuple((v * 100 + 127) // 255 for v in range(256))
# Color-select commands: b"#0" ... b"#255"
_COLOR_SELECT = tuple(f"#{i}".encode("ascii") for i in range(MAX_COLORS))

# bytes.translate() table: sixel value i (0-63) -> byte i + 0x3F
# Indices 64-255 are unused; zero-filled to meet the 256-byte requirement
_TRANSLATE_TABLE = bytes(range(_SIXEL_OFFSET, _SIXEL_OFFSET + 64)) + bytes(192)
# Cached single-byte bytes objects to avoid allocation in hot paths
_BYTE_CACHE = tuple(bytes((b,)) for b in range(256))

# Pre-built b"!N" strings for RLE counts up to 2048
_CACHED_COUNTS = 2048
_RLE_PREFIX = tuple(f"!{n}".encode("ascii") for n in range(_CACHED_COUNTS))

# Matches runs of 4+ identical bytes; shorter runs pass through re.sub untouched
_LONG_RUN_RE = re.compile(rb"(.)\1{3,}")
_NONZERO_RUN_RE = re.compile(rb"[^\x00]+")


QuantizeMethod: TypeAlias = Literal["fastoctree", "maxcoverage", "adaptive"]

_QUANTIZE_METHODS: dict[QuantizeMethod, PILImage.Quantize] = {
    "fastoctree": PILImage.Quantize.FASTOCTREE,
    "maxcoverage": PILImage.Quantize.MAXCOVERAGE,
    "adaptive": PILImage.Quantize.MEDIANCUT,
}

AnyBytes: TypeAlias = bytes | bytearray
Segment: TypeAlias = tuple[int, int, int]  # (start_col, end_col, color)
ColorSpans: TypeAlias = dict[int, tuple[int, int]]  # {color: (start_col, end_col)}
BackgroundColor: TypeAlias = tuple[int, int, int, float]  # (R, G, B, alpha)
AlphaMask: TypeAlias = bytes | None  # Per-pixel alpha values; zero means "skip this pixel"

_DEFAULT_BACKGROUND: BackgroundColor = (0, 0, 0, 1.0)


@dataclass(frozen=True)
class SixelOptions:
    """Options for sixel encoding.

    Attributes:
        colors: Number of colors to use (1-256). Fewer colors produce
            smaller output at the cost of image quality.
        smooth: Apply a spatial cleanup filter after quantization.
            Replaces scattered pixels with their neighborhood majority
            color, reducing output size at the cost of fine detail.
            ``None`` disables smoothing.  An odd integer (3, 5, 7, ...)
            sets the ModeFilter kernel size directly -- larger values
            produce smaller output but lose more detail.
        quantize: Quantization method. ``"fastoctree"`` is the default
            and works well at all image sizes.  ``"maxcoverage"`` produces
            20-29% smaller sixel output for images >= 64x64 because its
            colour allocation produces more spatially coherent regions,
            but is ~2x slower and allocates too many palette entries for
            very small images.  ``"adaptive"`` preserves Pillow's
            median-cut behavior.
        lazy_color_palette: When ``True``, color register definitions
            (``#N;2;R;G;B``) are emitted lazily, on first use of each
            register, and the freshly-defined register stays active for
            the next pixel run.  When ``False`` (the default), the full
            palette is defined up-front at the start of the sixel body
            and the rest of the stream only emits ``#N`` selections.
            Up-front definition produces a couple of extra bytes per
            color but renders correctly on terminals (e.g. WezTerm) that
            don't honor the spec rule that a freshly-defined register
            remains active.
    """

    colors: int = MAX_COLORS
    smooth: int | None = None
    quantize: QuantizeMethod = "fastoctree"
    lazy_color_palette: bool = False


_DEFAULT_SIXEL_OPTIONS = SixelOptions()


def image_to_sixels(
    image: PILImage.Image,
    options: SixelOptions | None = None,
    background: BackgroundColor | None = None,
) -> str:
    """Convert a PIL Image to a sixel-encoded string."""
    options = options or _DEFAULT_SIXEL_OPTIONS

    image, alpha_mask = _prepare_image(image, options, background)
    raw_data = image.tobytes()

    if _HAS_NUMPY:
        data, color_registers = _compact_palette_np(image, raw_data, alpha_mask)
    else:
        data, color_registers = _compact_palette(image, raw_data, alpha_mask)

    if options.lazy_color_palette:
        tracker: _ColorTracker = _LazyColorTracker(color_registers)
        palette_prefix = b""
    else:
        tracker = _PaletteColorTracker()
        palette_prefix = b"".join(color_registers)

    if _HAS_NUMPY:
        chunks = _iter_bands_np(data, image.width, image.height, tracker, alpha_mask)
    else:
        chunks = _iter_bands(data, image.width, image.height, tracker, alpha_mask)

    header = _make_header(image.width, image.height, transparent=alpha_mask is not None)
    return (header + palette_prefix + b"".join(chunks) + _ST).decode("ascii")


def _has_transparency(image: PILImage.Image) -> bool:
    """Check if an image has an alpha channel or palette transparency."""
    return image.mode in ("RGBA", "LA", "PA") or (image.mode == "P" and "transparency" in image.info)


def _composite_on_background(image: PILImage.Image, background: BackgroundColor) -> PILImage.Image:
    """Alpha-composite *image* onto *background*, returning an RGB image."""
    rgba = image.convert("RGBA")
    *bg_rgb, bg_alpha = background
    bg = PILImage.new("RGBA", rgba.size, (*bg_rgb, int(bg_alpha * 255)))
    return PILImage.alpha_composite(bg, rgba).convert("RGB")


def _prepare_image(
    image: PILImage.Image,
    options: SixelOptions,
    background: BackgroundColor | None,
) -> tuple[PILImage.Image, AlphaMask]:
    """Convert any image to paletted mode and optionally preserve transparent pixels."""
    alpha_mask: AlphaMask = None
    if _has_transparency(image):
        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A")
        alpha_hist = alpha.histogram()
        has_transparent = alpha_hist[0] > 0
        has_semitransparent = any(alpha_hist[1:255])

        if has_transparent:
            alpha_mask = alpha.tobytes()

        image = (
            _composite_on_background(rgba, background or _DEFAULT_BACKGROUND)
            if has_semitransparent
            else rgba.convert("RGB")
        )

    n_colors = options.colors
    small_palette = len(set(image.tobytes())) <= n_colors

    match image.mode:
        case "P" if small_palette:
            result = image
        case "L" if small_palette:
            result = image.convert("P")
        case _:
            result = _quantize_rgb_image(image.convert("RGB"), options)

    if smooth := options.smooth:
        result = result.filter(ImageFilter.ModeFilter(size=smooth))

    return result, alpha_mask


def _quantize_rgb_image(image: PILImage.Image, options: SixelOptions) -> PILImage.Image:
    """Quantize an RGB image using the method from *options*."""
    return image.quantize(colors=options.colors, method=_QUANTIZE_METHODS[options.quantize])


def _build_palette_map(palette: list[int], index_freq: dict[int, int]) -> tuple[dict[int, int], tuple[bytes, ...]]:
    """Build a remap table and register definitions from palette index frequencies.

    Returns ``(remap_dict, registers)`` where remap_dict maps old palette
    indices to new dense indices sorted by frequency.
    """
    to_pct = _RGB_TO_PCT
    to_triple: dict[int, tuple[int, int, int]] = {}
    triple_freq: Counter[tuple[int, int, int]] = Counter()

    for idx, freq in index_freq.items():
        triple = (to_pct[palette[idx * 3]], to_pct[palette[idx * 3 + 1]], to_pct[palette[idx * 3 + 2]])
        to_triple[idx] = triple
        triple_freq[triple] += freq

    ranked = sorted(triple_freq.items(), key=lambda x: (-x[1], x[0]))
    new_index = {triple: i for i, (triple, _) in enumerate(ranked)}

    remap = {idx: new_index[to_triple[idx]] for idx in index_freq}
    registers = tuple(f"#{i};2;{r};{g};{b}".encode("ascii") for i, ((r, g, b), _) in enumerate(ranked))

    return remap, registers


def _visible_color_counts(data: bytes, alpha_mask: AlphaMask) -> dict[int, int]:
    """Count palette indices that will actually be emitted."""
    if alpha_mask is None:
        return dict(Counter(data))

    return dict(Counter(color for color, alpha in zip(data, alpha_mask, strict=True) if alpha))


def _compact_palette(
    image: PILImage.Image,
    data: bytes,
    alpha_mask: AlphaMask = None,
) -> tuple[bytes, tuple[bytes, ...]]:
    """Deduplicate palette entries that round to the same sixel RGB percentage.

    and remap indices so the most frequent colours get the smallest numbers.
    """
    palette = image.getpalette() or []
    index_freq = _visible_color_counts(data, alpha_mask)
    remap, registers = _build_palette_map(palette, index_freq)

    table = bytearray(MAX_COLORS)
    for idx, new_idx in remap.items():
        table[idx] = new_idx

    return data.translate(bytes(table)), registers


def _make_header(width: int, height: int, transparent: bool = False) -> bytes:
    """Build the DCS header and raster attributes.

    P2=1 tells the terminal that 0-bits leave existing pixels unchanged, which
    is required when the image carries fully-transparent pixels we want to
    keep see-through.  Otherwise we use P2=0 so unset pixels fall back to the
    terminal's background color.
    """
    p2 = 1 if transparent else 0
    return f'\x1bP0;{p2};0q"1;1;{width};{height}'.encode("ascii")


@dataclass(slots=True)
class _PaletteColorTracker:
    """Reference-only tracker for palettes that were defined up-front.

    Returns ``#N`` when the active color changes and an empty string when
    the requested register is already active.
    """

    _active: int | None = None

    def select(self, color: int) -> AnyBytes:
        if color == self._active:
            return b""

        self._active = color
        return _COLOR_SELECT[color]


@dataclass(slots=True)
class _LazyColorTracker:
    """Defines color registers on first use; emits ``#N`` thereafter.

    The sixel spec lets a freshly defined register stay active, so a
    pixel run can immediately follow the definition without an extra
    ``#N`` selection.  Some terminals (notably WezTerm) ignore that rule
    and keep whatever color was active before the definition, which is
    why this mode is opt-in via ``SixelOptions.lazy_color_palette``.
    """

    _registers: tuple[bytes, ...]
    _defined: set[int] = field(default_factory=set)
    _active: int | None = None

    def select(self, color: int) -> AnyBytes:
        if color == self._active:
            return b""

        self._active = color
        if color in self._defined:
            return _COLOR_SELECT[color]

        self._defined.add(color)
        return self._registers[color]


_ColorTracker: TypeAlias = _PaletteColorTracker | _LazyColorTracker


def _iter_visible_pixels(
    row_bytes: bytes,
    row_alpha: bytes | None,
) -> Iterable[tuple[int, int]]:
    """Yield ``(x, color)`` pairs for pixels that should be emitted."""
    if row_alpha is None:
        return enumerate(row_bytes)

    return ((x, color) for x, (color, alpha) in enumerate(zip(row_bytes, row_alpha, strict=True)) if alpha)


def _pack_band(
    data: bytes,
    band_y: int,
    band_h: int,
    width: int,
    band_data: list[bytearray],
    alpha_mask: AlphaMask = None,
) -> ColorSpans:
    """Build per-color sixel bitmasks for one band.

    Returns ``{color: (first_col, last_col + 1)}`` for every active color.
    """
    span_start = [width] * MAX_COLORS
    span_end = [0] * MAX_COLORS

    for row in range(band_h):
        bit = 1 << row
        row_start = (band_y + row) * width
        row_bytes = data[row_start : row_start + width]
        row_alpha = None if alpha_mask is None else alpha_mask[row_start : row_start + width]

        for x, color in _iter_visible_pixels(row_bytes, row_alpha):
            band_data[color][x] |= bit
            if x < span_start[color]:
                span_start[color] = x
            if x >= span_end[color]:
                span_end[color] = x + 1

    return {c: (span_start[c], span_end[c]) for c in range(MAX_COLORS) if span_end[c]}


def _iter_greedy_passes(
    all_segments: list[Segment],
) -> tuple[list[Segment], list[Segment]]:
    """Extract one non-overlapping pass from sorted segments.

    Returns ``(pass_segments, remaining)`` where remaining segments
    still need further passes.
    """
    current_pass: list[Segment] = []
    remaining: list[Segment] = []
    cursor = 0

    for seg in all_segments:
        if seg[0] >= cursor:
            current_pass.append(seg)
            cursor = seg[1]
        else:
            remaining.append(seg)

    return current_pass, remaining


def _emit_repeat(count: int, char_byte: int) -> AnyBytes:
    """Emit *count* repetitions of a single sixel byte."""
    if count < _RLE_THRESHOLD:
        return _BYTE_CACHE[char_byte] * count

    return _rle_prefix(count) + _BYTE_CACHE[char_byte]


def _split_segments(spans: ColorSpans, band_data: list[bytearray]) -> list[Segment]:
    """Split color spans at internal gaps of >= _GAP_THRESHOLD empty columns.

    Iterates regex matches in a single pass, merging small gaps on the fly
    without building an intermediate list of runs. Skips the regex scan
    entirely when the span contains no zero bytes.
    """
    segments: list[Segment] = []
    for color, (start, end) in spans.items():
        row = band_data[color]

        # Fast path: no zeros in span means no gaps to split
        if row.find(0, start, end) == -1:
            segments.append((start, end, color))
            continue

        seg_start = -1
        seg_end = 0
        for m in _NONZERO_RUN_RE.finditer(row, start, end):
            ms, me = m.span()
            if seg_start == -1:
                seg_start = ms
                seg_end = me
            elif ms - seg_end < _GAP_THRESHOLD:
                seg_end = me
            else:
                segments.append((seg_start, seg_end, color))
                seg_start = ms
                seg_end = me

        if seg_start != -1:
            segments.append((seg_start, seg_end, color))

    return segments


def _emit_band(
    spans: ColorSpans,
    band_data: list[bytearray],
    tracker: _ColorTracker,
    band_h: int = _BAND_HEIGHT,
    allow_fill: bool = True,
) -> AnyBytes:
    """Encode one band, packing non-overlapping color spans into shared passes.

    Pass 0 uses the fillable optimization: segments are emitted as solid
    blocks (all bits set) that RLE-compress into short ``!N~`` runs.
    Subsequent passes emit real bitmask data which overwrites the filled
    pixels -- sixel 0-bits mean "no change", so correctness is preserved.

    Uses streaming greedy extraction to avoid materializing all passes
    at once, matching libsixel's NodeFlush pattern.
    """
    if not spans:  # pragma: no cover
        return _BYTE_CACHE[_NL]

    remaining = sorted(
        _split_segments(spans, band_data),
        key=lambda seg: (seg[0], seg[0] - seg[1], seg[2]),
    )

    # Fillable byte: all band_h bits set, offset to printable range
    fill_byte = _SIXEL_OFFSET + (1 << band_h) - 1

    buffer = bytearray()
    fillable = allow_fill

    while remaining:
        pass_segments, remaining = _iter_greedy_passes(remaining)

        cursor = 0
        for start, end, color in pass_segments:
            buffer.extend(tracker.select(color))
            if start > cursor:
                buffer.extend(_emit_repeat(start - cursor, _SIXEL_OFFSET))
            if fillable:
                buffer.extend(_emit_repeat(end - start, fill_byte))
            else:
                buffer.extend(_rle_encode(band_data[color], start, end))
            cursor = end

        fillable = False
        if remaining:
            buffer.append(_CR)

    buffer.append(_NL)
    return buffer


def _iter_bands(
    data: bytes,
    width: int,
    height: int,
    tracker: _ColorTracker,
    alpha_mask: AlphaMask = None,
) -> list[AnyBytes]:
    """Return encoded sixel chunks, one per band."""
    band_data = [bytearray(width) for _ in range(MAX_COLORS)]
    zero_fill = bytes(width)
    allow_fill = alpha_mask is None

    bands: list[AnyBytes] = []
    for band_y in range(0, height, _BAND_HEIGHT):
        band_h = min(_BAND_HEIGHT, height - band_y)
        spans = _pack_band(data, band_y, band_h, width, band_data, alpha_mask)
        bands.append(_emit_band(spans, band_data, tracker, band_h, allow_fill=allow_fill))

        for c in spans:
            band_data[c][:] = zero_fill

    return bands


def _rle_prefix(n: int) -> bytes:
    return _RLE_PREFIX[n] if n < _CACHED_COUNTS else f"!{n}".encode("ascii")


def _compress_long_run(match: re.Match[bytes]) -> bytes:
    """``re.sub`` callback: compress a run of 4+ identical bytes to ``!N<char>``."""
    n = match.end() - match.start()
    return _rle_prefix(n) + match.group(1)


def _rle_encode(data: bytearray, start: int, end: int) -> AnyBytes:
    """RLE-encode ``data[start:end]`` with the +0x3F sixel offset applied."""
    if segment := data[start:end].translate(_TRANSLATE_TABLE):
        return _LONG_RUN_RE.sub(_compress_long_run, segment)
    return b""  # pragma: no cover


if _HAS_NUMPY:
    # Bit weights for the 6 rows in a sixel band: [1, 2, 4, 8, 16, 32]
    _NP_BIT_WEIGHTS = np.array([1 << r for r in range(_BAND_HEIGHT)], dtype=np.uint8)

    def _compact_palette_np(
        image: PILImage.Image,
        data: bytes,
        alpha_mask: AlphaMask = None,
    ) -> tuple[bytes, tuple[bytes, ...]]:
        """Numpy-accelerated palette compaction using ``np.bincount``."""
        palette = image.getpalette() or []
        arr = np.frombuffer(data, dtype=np.uint8)
        visible_arr = arr if alpha_mask is None else arr[np.frombuffer(alpha_mask, dtype=np.uint8) != 0]
        counts_arr = np.bincount(visible_arr, minlength=MAX_COLORS)

        index_freq = {int(i): int(counts_arr[i]) for i in np.flatnonzero(counts_arr)}
        remap_dict, registers = _build_palette_map(palette, index_freq)

        remap = np.zeros(MAX_COLORS, dtype=np.uint8)
        for idx, new_idx in remap_dict.items():
            remap[idx] = new_idx

        return remap[arr].tobytes(), registers

    def _iter_bands_np(
        data: bytes,
        width: int,
        height: int,
        tracker: _ColorTracker,
        alpha_mask: AlphaMask = None,
    ) -> list[AnyBytes]:
        """Return encoded sixel chunks using numpy-accelerated band packing.

        Uses band-major reshaping for cache locality: the pixel array is
        padded to a multiple of 6 rows and reshaped to (n_bands, 6, width)
        so each band is contiguous in memory.

        Uses ``np.add.at`` to scatter bit weights into a (MAX_COLORS, width)
        bitmask array -- replacing the per-pixel Python loop in ``_pack_band``.
        """
        band_data = [bytearray(width) for _ in range(MAX_COLORS)]
        zero_fill = bytes(width)
        allow_fill = alpha_mask is None

        arr = np.frombuffer(data, dtype=np.uint8).reshape(height, width)
        mask_arr = None if alpha_mask is None else np.frombuffer(alpha_mask, dtype=np.uint8).reshape(height, width)

        # Pad height to a multiple of 6 and reshape to (n_bands, 6, width)
        pad_h = (_BAND_HEIGHT - height % _BAND_HEIGHT) % _BAND_HEIGHT
        if pad_h:
            arr = np.pad(arr, ((0, pad_h), (0, 0)), constant_values=0)
            if mask_arr is not None:
                mask_arr = np.pad(mask_arr, ((0, pad_h), (0, 0)), constant_values=0)
        band_arr = arr.reshape(-1, _BAND_HEIGHT, width)
        band_mask_arr = None if mask_arr is None else mask_arr.reshape(-1, _BAND_HEIGHT, width)
        n_bands = band_arr.shape[0]

        bitmask = np.zeros((MAX_COLORS, width), dtype=np.uint8)
        cols = np.arange(width)

        # Last band may be partial (fewer than 6 real rows)
        last_band_h = _BAND_HEIGHT - pad_h if pad_h else _BAND_HEIGHT

        bands: list[AnyBytes] = []
        for band_idx in range(n_bands):
            band = band_arr[band_idx]
            band_h = last_band_h if band_idx == n_bands - 1 else _BAND_HEIGHT
            band_mask = None if band_mask_arr is None else band_mask_arr[band_idx]

            # Scatter bit weights into the bitmask array (up to 6 vectorized passes)
            for row in range(band_h):
                visible = slice(None) if band_mask is None else band_mask[row] != 0
                np.add.at(bitmask, (band[row, visible], cols[visible]), _NP_BIT_WEIGHTS[row])

            # Identify active colors and compute horizontal spans
            active_colors = np.flatnonzero(np.any(bitmask, axis=1))
            active_rows = bitmask[active_colors]  # (n_active, width)
            nonzero = active_rows > 0
            first_cols = np.argmax(nonzero, axis=1)
            last_cols = width - 1 - np.argmax(nonzero[:, ::-1], axis=1)

            # Every color returned by np.unique exists in the band, so
            # the bitmask row is guaranteed to have nonzero data
            spans: ColorSpans = {}
            for i, c_np in enumerate(active_colors):
                c = int(c_np)
                spans[c] = (int(first_cols[i]), int(last_cols[i]) + 1)
                band_data[c][:] = active_rows[i].tobytes()

            bands.append(_emit_band(spans, band_data, tracker, band_h, allow_fill=allow_fill))

            for c in spans:
                band_data[c][:] = zero_fill
            bitmask[active_colors] = 0

        return bands

else:  # pragma: no cover

    def _compact_palette_np(
        image: PILImage.Image,
        data: bytes,
        alpha_mask: AlphaMask = None,
    ) -> tuple[bytes, tuple[bytes, ...]]:
        """Fallback to the pure-Python palette compactor when NumPy is unavailable."""
        return _compact_palette(image, data, alpha_mask)

    def _iter_bands_np(
        data: bytes,
        width: int,
        height: int,
        tracker: _ColorTracker,
        alpha_mask: AlphaMask = None,
    ) -> list[AnyBytes]:
        """Fallback to the pure-Python band iterator when NumPy is unavailable."""
        return _iter_bands(data, width, height, tracker, alpha_mask)
