# pen-plotter-art

A Python framework for generating pen plotter art. Write a generative art piece as a list of polylines, and the framework converts it to SVG and HPGL output, then opens an interactive animation showing how the plotter will draw it.

## Setup

1. Install [Python](https://www.python.org/downloads/macos/)
1. Open [Terminal](https://support.apple.com/guide/terminal/open-or-quit-terminal-apd5265185d-f365-44cb-8b09-71a064a42125/mac)

```sh
python3 -m venv venv
source venv/bin/activate
pip install matplotlib vpype
```

## Running

```sh
python main.py --art spiral
```

The `--art` flag specifies the name of a folder inside `art/`. The program will:

1. Call `generate_lines()` from `art/<name>/generate.py`
1. Write `art/<name>/renders/<name>.svg` and `art/<name>/renders/<name>.hpgl`
1. Open an interactive preview animation of the plotter drawing the piece

## Project Structure

```
main.py              # Entry point — orchestrates generation, export, and preview
draw.py              # Converts lines to a vpype document, writes SVG and HPGL
preview.py           # Reads the HPGL file and animates the plotter path with matplotlib
hpgl/
  hpgl.py            # HPGL parser used by the preview
  fonts.py           # Optional font helpers
art/
  spiral/            # An art piece named "spiral"
    generate.py      # Defines generate_lines(width, height) -> list[list[tuple]]
    renders/
      spiral.svg     # Generated SVG output
      spiral.hpgl    # Generated HPGL output
```

## Creating an Art Piece

Create a new folder under `art/` and add a `generate.py` file that exports a single function:

```python
def generate_lines(width, height):
    """
    width, height: page dimensions in mm (default A4: 210 x 297)
    Returns a list of polylines, where each polyline is a list of (x, y) tuples in mm.
    """
    ...
    return [points]
```

Each polyline is a continuous pen-down stroke. The plotter lifts the pen between polylines.

**Keep connected points in a single polyline.** A wiggly line made of thousands of points should be one polyline — not thousands of 2-point polylines. If you split it into segments, the plotter lifts and drops the pen at every join, which is slow and produces visible marks at each touch-down point.

```python
# Good — one stroke, pen never lifts
return [[(x1,y1), (x2,y2), (x3,y3), (x4,y4), ...]]

# Bad — pen lifts between every segment
return [[(x1,y1),(x2,y2)], [(x2,y2),(x3,y3)], [(x3,y3),(x4,y4)], ...]
```

Use multiple polylines only for genuinely separate strokes (e.g. the outline of a shape vs. an inner detail).

**Example** — a diagonal line across the page:

```python
def generate_lines(width, height):
    return [[(0, 0), (width, height)]]
```

Then run it:

```sh
python main.py --art my_piece
```

## Configuration

Plotter settings are at the top of `main.py`:

| Variable           | Default       | Description                                           |
| ------------------ | ------------- | ----------------------------------------------------- |
| `WIDTH` / `HEIGHT` | `210` / `297` | Page size in mm (A4 portrait)                         |
| `HPGL_DEVICE`      | `"hp7475a"`   | vpype device name (controls plotter units and limits) |
| `HPGL_PAGE_SIZE`   | `"a4"`        | Paper size passed to vpype                            |
| `HPGL_LANDSCAPE`   | `True`        | Rotate output to landscape                            |
| `HPGL_CENTER`      | `True`        | Center the drawing on the page                        |
| `DRAW_SPEED`       | `40.0`        | Pen-down speed in mm/s (for preview timing)           |
| `TRAVEL_SPEED`     | `200.0`       | Pen-up speed in mm/s (for preview timing)             |

Supported `HPGL_DEVICE` values include: `hp7475a`, `hp7550`, `hp7440a`, `designmate`, `artisan`, `dmp_161`, `dxy`, `sketchmate`.

## Resources

- https://paulbourke.net/dataformats/hpgl/
- https://vpype.readthedocs.io/en/latest/
- https://matplotlib.org/