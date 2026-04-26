#!/usr/bin/env python

"""Run the textual_image demo."""

from pathlib import Path
import sys
from argparse import ArgumentParser
from importlib.util import find_spec

from textual_image.demo.renderable import RENDERING_METHODS

textual_available = bool(find_spec("textual"))
default_mode = "rich" if find_spec("textual") is None else "textual"

def path_exists(path_str: str) -> Path:
    """Check if the provided path exists and is a file."""
    path = Path(path_str)
    if not path.is_file():
        raise ValueError(f"The provided path '{path_str}' does not exist or is not a file.")
    return path

parser = ArgumentParser(description="Demo the capabilities of textual-image")
parser.add_argument("mode", choices=["rich", "textual"], nargs="?", default=default_mode)
parser.add_argument("-m", "--method", choices=RENDERING_METHODS.keys(), default="auto")
parser.add_argument("--image", help="Path to an image file to use for the demo. If not provided, a default image will be used.", default=Path(__file__).parent / "gracehopper.jpg", type=path_exists)
parser.add_argument("--transparent", action="store_true", help="Use a transparent background for the demo (only applicable to the Textual mode).")
arguments = parser.parse_args()

if arguments.mode == "rich":
    from textual_image.demo import renderable

    renderable.TEST_IMAGE = Path(arguments.image)

    renderable.run(arguments.method)
elif not textual_available:
    sys.stderr.write(
        "Optional Textual dependency not available. Install this package as `textual-image[textual]` for Textual support."
    )
else:
    from textual_image.demo import widget

    widget.TEST_IMAGE = Path(arguments.image)

    widget.run(arguments.method, transparent=arguments.transparent)
