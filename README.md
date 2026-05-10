# pen-plotter-art

A Python framework for generating pen plotter art. Write a generative art piece using the [vsketch](https://vsketch.readthedocs.io/en/latest/) API, and the framework converts it to SVG and HPGL output, then opens an interactive animation showing how the plotter will draw it.

## Setup

1. Install [Python](https://www.python.org/downloads/macos/)
2. Open [Terminal](https://support.apple.com/guide/terminal/open-or-quit-terminal-apd5265185d-f365-44cb-8b09-71a064a42125/mac) in this folder
3. Run:

```sh
make install
```

This creates a `venv/` and installs all dependencies from `requirements.txt`. You only need to do this once.

## Generating Art

```sh
make run
```

Pick an art piece from the interactive menu. Or pass one directly:

```sh
make run ART=spiral
make run ART=spiral CONFIG=my_config.json
```

Each "art piece" uses `art/<name>/generate.py` to draw using the [vsketch](https://vsketch.readthedocs.io/en/latest/overview.html) API.

The framework passes the drawing to [vpype](https://vpype.readthedocs.io/en/latest/) to produce SVG and HPGL files, creating (or overwriting) two files:
- `art/<name>/renders/<name>.svg` 
- `art/<name>/renders/<name>.hpgl`

The program then _reads_ that HPGL file and "previews" what the pen plotter will do.

## Creating an Art Piece

Create a new folder under `art/` and add a `generate.py` file that exports a single function:

```python
def generate(vsk, width, height):
    """
    vsk:    a vsketch.Vsketch instance — draw into it using the vsketch API.
            Coordinates are in mm (scale("1mm") is pre-applied by the framework).
    width, height: plottable area in mm (slightly smaller than the raw paper size).
    """
    vsk.line(0, 0, width, height)
```

The full [vsketch API](https://vsketch.readthedocs.io/en/latest/overview.html) is available: `vsk.line()`, `vsk.rect()`, `vsk.circle()`, `vsk.polygon()`, `vsk.geometry()` (Shapely objects), transforms (`vsk.translate()`, `vsk.rotate()`, `vsk.pushMatrix()`), randomness (`vsk.random()`, `vsk.randomGaussian()`, `vsk.noise()`), and more.

**Example** — a diagonal line across the page:

Create `art/my_piece` and `art/my_piece/generate.py`

```python
def generate(vsk, width, height):
    vsk.line(0, 0, width, height)
```

Then run the program:

```sh
make run ART=my_piece
```

## Configuring the "Plotter"

Plotter settings are at the top of `main.py`:

| Variable           | Default       | Description                                           |
| ------------------ | ------------- | ----------------------------------------------------- |
| `WIDTH` / `HEIGHT` | `210` / `297` | Page size in mm (A4 portrait)                         |
| `HPGL_DEVICE`      | `"hp7475a"`   | [vpype device](https://vpype.readthedocs.io/en/latest/reference.html#write) name (controls plotter units and limits) |
| `HPGL_PAGE_SIZE`   | `"a4"`        | Paper size passed to vpype                            |
| `HPGL_LANDSCAPE`   | `True`        | Rotate output to landscape                            |
| `HPGL_CENTER`      | `True`        | Center the drawing on the page                        |
| `DRAW_SPEED`       | `40.0`        | Pen-down speed in mm/s (for preview timing)           |
| `TRAVEL_SPEED`     | `200.0`       | Pen-up speed in mm/s (for preview timing)             |

Supported `HPGL_DEVICE` values include: `hp7475a`, `hp7550`, `hp7440a`, `designmate`, `artisan`, `dmp_161`, `dxy`, `sketchmate`.

## Resources

- https://vsketch.readthedocs.io/en/latest/overview.html
- https://paulbourke.net/dataformats/hpgl/
- https://vpype.readthedocs.io/en/latest/
- https://matplotlib.org/
- [One Formula That Demystifies 3D Graphics](https://www.youtube.com/watch?v=qjWkNZ0SXfo)

## Tips

### Continuous Strokes

Each stroke is a continuous pen-down move. The plotter lifts the pen between separate shapes.

**Keep connected points in a single stroke.** A wiggly line made of thousands of points should be one continuous path — not thousands of tiny segments. If you split it up, the plotter lifts and drops the pen at every join, which is slow and produces visible marks at each touch-down point.

Use `vsk.polygon(xs, ys)` or `vsk.geometry(LineString(points))` to draw long connected paths efficiently:

```python
from shapely.geometry import LineString

# Good — one continuous stroke, pen never lifts
vsk.geometry(LineString([(x1,y1), (x2,y2), (x3,y3), (x4,y4), ...]))
```

Use separate draw calls only for genuinely separate strokes (e.g. the outline of a shape vs. an inner detail).
