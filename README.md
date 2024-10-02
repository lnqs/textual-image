# textual-image

**Render images directly in your terminal using [Textual](https://www.textualize.io/) and [Rich](https://github.com/Textualize/rich).**

![Demo App](./demo.gif)

_textual-image_ offers both Rich renderables and Textual Widgets that leverage the [Terminal Graphics Protocol (TGP)](https://sw.kovidgoyal.net/kitty/graphics-protocol/) and [Sixel](https://en.wikipedia.org/wiki/Sixel) protocols to display images in your terminal. For terminals that don't support these protocols, fallback rendering using Unicode characters is available.

## Supported Terminals

- **Terminal Graphics Protocol (TGP)**: Initially introduced by the [Kitty](https://sw.kovidgoyal.net/kitty/) terminal emulator, fully supported in Kitty, and largely implemented in [WezTerm](https://wezfurlong.org/wezterm/index.html) and partially supported by [Konsole](https://konsole.kde.org/) and [wayst](https://github.com/91861/wayst).
- **Sixel Graphics**: Supported by various terminal emulators including [xterm](https://invisible-island.net/xterm/) and others.

_Note_: Testing has been conducted primarily using Kitty for TGP and xterm for Sixel on Linux, with some sanity checks on other terminals. Feedback and interoperability testing on other terminal emulators and operating systems would be highly valued.

See the Support Matrix below on what was tested already.

### Support Matrix [^1]

| Terminal            | TPG support | Sixel support | Works with textual-image |
|---------------------|:-----------:|:-------------:|:------------------------:|
| Alacritty           |          ❌ |            ❌ |                          |
| Black Box           |          ❌ |            ✅ |                       ⚫ |
| Bobcat              |          ❌ |            ✅ |                       ⚫ |
| ConEmu              |          ❌ |            ❌ |                          |
| Contour             |          ❌ |            ✅ |                       ⚫ |
| ctx terminal        |          ❌ |            ✅ |                       ⚫ |
| Darktile            |          ❌ |            ✅ |                       ⚫ |
| DomTerm             |          ❌ |            ✅ |                       ⚫ |
| Eat                 |          ❌ |            ✅ |                       ⚫ |
| Elementary Terminal |          ❌ |            ❌ |                          |
| foot                |          ❌ |            ✅ |                       ✅ |
| GNOME Terminal      |          ❌ |            ❌ |                          |
| guake               |          ❌ |            ❌ |                          |
| iTerm2              |          ❌ |            ✅ |                       ⚫ |
| kitty               |          ✅ |            ❌ |                       ✅ |
| konsole             |          ✅ |            ✅ |                   ❓[^2] |
| LaTerminal          |          ❌ |            ✅ |                       ⚫ |
| MacTerm             |          ❌ |            ✅ |                       ⚫ |
| mintty              |          ❌ |            ✅ |                       ⚫ |
| mlterm              |          ❌ |            ✅ |                       ⚫ |
| MobaXterm           |          ❌ |            ❌ |                          |
| PuTTY               |          ❌ |            ❌ |                          |
| Rio terminal        |          ❌ |            ❌ |                          |
| Rlogin              |          ❌ |            ✅ |                       ⚫ |
| suckless st         |          ❌ |            ❌ |                          |
| SwiftTerm           |          ❌ |            ✅ |                       ⚫ |
| SyncTERM            |          ❌ |            ✅ |                       ⚫ |
| TeraTerm            |          ❌ |            ❌ |                          |
| Terminal.app        |          ❌ |            ❌ |                          |
| Terminology         |          ❌ |            ❌ |                          |
| termux              |          ❌ |            ❌ |                          |
| Tilix               |          ❌ |            ❌ |                          |
| tmux                |          ❌ |            ✅ |                   ✅[^3] |
| toyterm             |          ❌ |            ✅ |                       ⚫ |
| URxvt               |          ❌ |            ❌ |                          |
| U++                 |          ❌ |            ✅ |                       ⚫ |
| Visual Studio Code  |          ❌ |            ✅ |                   ✅[^4] |
| wayst               |          ✅ |            ✅ |                   ❓[^5] |
| wezterm             |          ✅ |            ✅ |                   ❓[^6] |
| Windows Console     |          ❌ |            ❌ |                          |
| Windows Terminal    |          ❌ |            ✅ |                       ⚫ |
| xfce-terminal       |          ❌ |            ✅ |                       ⚫ |
| xterm               |          ❌ |            ✅ |                       ✅ |
| xterm.js            |          ❌ |            ✅ |                       ⚫ |
| yaft                |          ❌ |            ✅ |                       ⚫ |
| Yakuake             |          ❌ |            ✅ |                       ⚫ |
| Zellij              |          ❌ |            ✅ |                   ❌[^7] |

✅ = Supported; ❌ = Not Supported; ⚫ = To Be Tested; ❓ = Works, but with glitches (further investigation needed)

[^1]: Based on [Are We Sixel Yet?](https://www.arewesixelyet.com/)
[^2]: Reports to support TGP but doesn't draw images. If set to Sixel explicitly, it works besides a few minor glitches.
[^3]: Works only in a Sixel enabled terminal, TGP does not work with tmux.
[^4]: The `terminal.integrated.enableImages` setting has to be enabled.
[^5]: Both TGP and Sixel draw graphics, but only with major glitches.
[^6]: TGP draws graphics, but with major glitches; Sixel works fine but doesn't get auto-selected due to reporting TGP support.
[^7]: Reports to support Sixel, but doesn't draw anything.

### Enabling Sixel Support on xterm

Sixel on xterm is disabled by default. To enable it, add `+lc` and `-ti vt340` options when launching xterm:

```sh
xterm +lc -ti vt340
```

Alternatively, you can add these options to your xterm configuration file (`~/.Xresources` or `~/.Xdefaults`) to make the change permanent:

```sh
echo 'XTerm*decTerminalID: vt340' >> ~/.Xresources
xrdb -merge ~/.Xresources
```

## Installation

Install _textual-image_ using pip with the following commands:

For the basic installation:
```sh
pip install textual-image
```

To include the Textual Widget's dependencies:
```sh
pip install textual-image[textual]
```

## Demonstration

Once installed, run the demo application to see the module in action.

For a demonstration of the Rich renderable, use:
```sh
python -m textual_image rich
```

For a demonstration of the Textual Widget, use:
```sh
python -m textual_image textual
```

The module will automatically select the best available rendering option. If you wish to specify a particular rendering method, use the `-p` argument with one of the following values: `tgp`, `sixel`, `halfcell`, or `unicode`.

For more information, use:
```sh
python -m textual_image --help
```

## Usage

### Rich Integration

To use the Rich renderable, simply pass an instance of `textual_image.renderable.Image` to a Rich function that renders data:

```python
from rich.console import Console
from textual_image.renderable import Image

console = Console()
console.print(Image("path/to/image.png"))
```

The `Image` constructor accepts either a string, a `pathlib.Path` representing the file path of an image readable by [Pillow](https://python-pillow.org/), or a Pillow `Image` instance directly.

By default, the image is rendered in its original dimensions. You can modify this behavior by specifying the `width` and/or `height` parameters. These can be defined as an integer (number of cells), a percentage string (e.g., `50%`), or the literal `auto` to automatically scale while maintaining the aspect ratio.

`textual_image.renderable.Image` defaults to the best available rendering method. To specify an explicit rendering method, use one of the following classes: `textual_image.renderable.tgp.Image`, `textual_image.renderable.sixel.Image`, `textual_image.renderable.halfcell.Image`, or `textual_image.renderable.unicode.Image`.

### Textual Integration

For integration with Textual, _textual-image_ offers a Textual `Widget` to render images:

```python
from textual.app import App, ComposeResult
from textual_image.widget import Image

class ImageApp(App[None]):
    def compose(self) -> ComposeResult:
        yield Image("path/to/image.png")

ImageApp().run()
```

The `Image` constructor accepts either a string or a `pathlib.Path` with the file path of an image readable by [Pillow](https://python-pillow.org/), or a Pillow `Image` instance directly.

You can also set the image using the `image` property of an `Image` instance:

```python
from textual.app import App, ComposeResult
from textual_image.textual import Image

class ImageApp(App[None]):
    def compose(self) -> ComposeResult:
        image = Image()
        image.image = "path/to/image.png"
        yield image

ImageApp().run()
```

If a different image is set, the Widget will update to display the new image.

By default, the best available rendering option is used. To override this, you can instantiate `textual_image.widget.TGPImage`, `textual_image.widget.SixelImage`, `textual_image.widget.HalfcellImage`, or `textual_image.widget.UnicodeImage` directly.

_*Note*_: The process of determining the best available rendering option involves querying the terminal, which means sending and receiving data. Since Textual starts threads to handle input and output, this query will **not work** once the Textual app has started. Therefore, make sure that `textual_image.renderable` is imported **before** running the Textual app (which is typically the case in most use cases).

## Limitations

- **Sixel Support in Textual**: Sixel support in Textual is not particularly performant due to the way Textual handles rendering. The Sixel graphics are injected into the rendering process in a somewhat hacky manner, which affects performance. Scrolling and changing styles of images can lead to a lot of flickering. But for mostly static images it should work fine. If not, please file an issue on GitHub.

## Contribution

If you find this module useful, please consider starring the repository on GitHub.

This project began by moving some TGP functionality from a private project to a public GitHub repository and PyPI package, with some additional code added along the way to support Sixel graphics. If you encounter any issues, please file an issue on GitHub.

Contributions via pull requests are welcome and encouraged.
