#!/usr/bin/env python

"""Run the textual_kitty demo."""

from argparse import ArgumentParser
from importlib.util import find_spec

from textual_kitty.demo import renderable, widget

default_mode = "rich" if find_spec("textual") is None else "textual"

parser = ArgumentParser(description="Demo the capabilities of textual-kitty")
parser.add_argument("mode", choices=["rich", "textual"], nargs="?", default=default_mode)
parser.add_argument("-m", "--method", choices=[m.name for m in renderable.RenderingMethods], default="auto")
arguments = parser.parse_args()

if arguments.mode == "rich":
    renderable.run(renderable.RenderingMethods[arguments.method])
else:
    widget.run(widget.RenderingMethods[arguments.method])
