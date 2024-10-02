#!/usr/bin/env python

"""Run the textual_image demo."""

import sys
from argparse import ArgumentParser
from importlib.util import find_spec

from textual_image.demo.renderable import RENDERING_METHODS

textual_available = bool(find_spec("textual"))
default_mode = "rich" if find_spec("textual") is None else "textual"

parser = ArgumentParser(description="Demo the capabilities of textual-image")
parser.add_argument("mode", choices=["rich", "textual"], nargs="?", default=default_mode)
parser.add_argument("-m", "--method", choices=RENDERING_METHODS.keys(), default="auto")
arguments = parser.parse_args()

if arguments.mode == "rich":
    from textual_image.demo.renderable import run as run_rich_demo

    run_rich_demo(arguments.method)
elif not textual_available:
    sys.stderr.write(
        "Optional Textual dependency not available. Install this package as `textual-image[textual]` for Textual support."
    )
else:
    from textual_image.demo.widget import run as run_textual_demo

    run_textual_demo(arguments.method)
