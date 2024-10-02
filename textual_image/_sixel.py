from itertools import groupby

from PIL import Image as PILImage

from textual_image._utils import grouped

DCS = "\x1bP"
ST = "\x1b\\"
COLORS = 256


def image_to_sixels(image: PILImage.Image) -> str:
    """Convert an image to Sixels.

    This function convert a `PIL.Image.Image` into the Sixel format.

    Args:
        image: Image to convert to Sixels

    Returns:
        The `image` as Sixel data.
    """
    image = image.convert("RGB").convert("P", palette=PILImage.Palette.ADAPTIVE, colors=COLORS)

    return "".join(
        [
            _get_header(image),
            _get_body(image),
            _get_terminator(),
        ]
    )


def _get_header(image: PILImage.Image) -> str:
    # See <https://vt100.net/docs/vt3xx-gp/chapter14.html#S14.2.1> for details about the parameters.
    sixel_mode = f"{DCS}0;0;0"
    raster_attributes = f'q"1;1;{image.width};{image.height}'

    color_registers = []
    for i, color in enumerate(grouped(image.getpalette() or [], 3)):
        color_str = ";".join(str(int(channel / 256 * 100)) for channel in color)
        color_registers.append(f"#{i};2;{color_str}")

    return f'{sixel_mode}{raster_attributes}{"".join(color_registers)}'


def _get_body(image: PILImage.Image) -> str:
    tokens = []

    for y, row in enumerate(grouped(image.getdata(), image.width)):
        n = 1 << y % 6
        for color, group in groupby(row):
            tokens.append(f"#{color}")

            count = len(list(group))
            if count < 3:
                tokens.append(chr(0x3F + n) * count)
            else:
                tokens.append(f"!{count}{chr(0x3F + n)}")

        tokens.append("-" if n == 32 else "$")

    return "".join(tokens)


def _get_terminator() -> str:
    return ST
