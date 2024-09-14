# textual-kitty

Render images in the terminal with [Textual](https://www.textualize.io/) and [rich](https://github.com/Textualize/rich).

![Demo App](./demo.jpg)

_textual-kitty_ provides a rich _renderable_ and a Textual Widget utilizing the [Terminal Graphics Protocol](https://sw.kovidgoyal.net/kitty/graphics-protocol/) to display images in terminals. 

## Supported Terminals

The _Terminal Graphics Protocol_ was introduced by [Kitty](https://sw.kovidgoyal.net/kitty/) is is fully supported in this terminal.
[WezTerm](https://wezfurlong.org/wezterm/index.html) has a mostly complete implementation. [Konsole](https://konsole.kde.org/) and [wayst](https://github.com/91861/wayst) have partial support.

However, this module was only tested with _Kitty_. Feedback for other terminals is welcome.

## Installing

Install _textual-kitty_ via pip:

```
pip install textual-kitty
```

## Demo

Clone this repository and run

```
./demo rich
```

for a demo of the _rich_ renderable or

```
./demo textual
```

for a demo of the _Textual_ Widget.

## Usage

### rich

Just pass a `textual_kitty.rich.Image` instance to a _rich_ function rendering data:

```python
from rich.console import Console
from textual_kitty.rich import Image

console = Console()
console.print(Image("path/to/image.png"))
```

The `Image` constructor accepts a `str` or `pathlib.Path` with a file path of an image file readable by [Pillow](https://python-pillow.org/) or a Pillow `Image` instance.

Per default, the image will render full terminal width or the width of the parent container. A `width` parameter can be passed to the constructor to overwrite this behaviour and explicitly specify the width of the image in terminal cells.
The aspect ratio of the image will be kept in both cases. 

### Textual

_textual-python_ provides an Textual `Widget` to render images:

```python
from textual.app import App, ComposeResult
from textual_kitty.textual import Image

class ImageApp(App[None]):
    def compose(self) -> ComposeResult:
        yield Image("path/to/image.png")

ImageApp().run()
```

The `Image` constructor accepts a `str` or `pathlib.Path` with a file path of an image file readable by [Pillow](https://python-pillow.org/) or a Pillow `Image` instance.

Additionally, the image can be set with the `image` property of an `Image` instance:

```python
from textual.app import App, ComposeResult
from textual_kitty.textual import Image

class ImageApp(App[None]):
    def compose(self) -> ComposeResult:
        image = Image()
        image.image = "path/to/image.png"
        yield image

ImageApp().run()
```

If another image was set before, the Widget updates to display the new data.

The `Image` constructor accepts a `load_async` parameter. If set to `True`, the first render of the image (and subsequent after a resize) will not actually render the image, but start processing the image data and sending it to the terminal asynchronously. The Widget will update itself after this is done to show the image. A loading indicator is shown during processing. This helps keeping the app responsive if large images are passed to this class.
But it does come with with the overhead of double the update cycles and running asynchronously tasks.

## Contribution

If you find this module helpful, please leave this repository a star.

For now, I just moved this functionality from a private project to a public GitHub repo/PyPI package. It workds fine for my usecase, please fill a bug ticket if you encounter unexpected behaviour.

And, of course, pull requests are welcome.