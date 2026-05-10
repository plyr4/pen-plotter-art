# pen-plotter-art

A small program for generating pen plotter art.

Write a generative art sketch using Python, render it to [SVG](https://developer.mozilla.org/en-US/docs/Web/SVG) and [HPGL](https://en.wikipedia.org/wiki/HP-GL), then preview the HPGL with an interactive animation showing how the plotter will draw it.

## Setup

* [Python 3.13.1](https://www.python.org/downloads/macos/)
* [pip](https://pip.pypa.io/en/stable/installation/)
* [Make](https://www.gnu.org/software/make/)

```bash
$ make install
```

This creates a `venv/` and installs all dependencies from `requirements.txt`. You only need to do this once.

## Viewing a Sketch

```bash
$ make run
? Select an art piece: (Use arrow keys)
 » cube
```

Pick an art piece from `art/`. Or pass one directly:

```bash
$ make run spiral
```

Each art piece lives in `art/<name>/generate.py` and is a `vsketch.SketchClass` subclass.

The program runs the sketch, passes the drawing through [vpype](https://vpype.readthedocs.io/en/latest/) to produce output files, then previews the HPGL as an animation:

- `art/<name>/renders/<name>.svg`
- `art/<name>/renders/<name>.hpgl`

After generating, it prints a stroke analysis table (strokes, segments, points, pen-down distance, pen-up travel) and opens the preview.

## Creating a New Sketch

```bash
$ make new
? Name your new art piece: cool_piece
```

You can also pass the sketch name directly:

```bash
$ make new my_piece
```

`make new` uses [cookiecutter](https://cookiecutter.readthedocs.io/en/stable/) with the local `sketch_template/`, which is based on the [vsketch cookiecutter template](https://github.com/abey79/cookiecutter-vsketch-sketch). It generates a new folder under `art/` with a ready-to-edit `generate.py`.


### Editing a Sketch

Open `art/<name>/generate.py` and implement the `draw` method:

```python
class MyPieceSketch(vsketch.SketchClass):
    # declare interactive parameters here
    radius = vsketch.Param(2.0)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a4", landscape=True)
        vsk.scale("1cm")

        # draw using the vsketch API
        vsk.circle(0, 0, self.radius, mode="radius")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype(
            "linemerge --tolerance 0.5mm linesimplify --tolerance 0.1mm linesort reloop --tolerance 0.05mm"
        )
```

The `finalize` method (pre-filled by the template) runs a vpype pipeline with sensible defaults for line merging, simplification, sorting, and relooping tolerances. Adjust tolerances as needed for your sketch.

The full [vsketch API](https://vsketch.readthedocs.io/en/latest/overview.html) is available: `vsk.line()`, `vsk.rect()`, `vsk.circle()`, `vsk.polygon()`, `vsk.geometry()` (Shapely objects), transforms (`vsk.translate()`, `vsk.rotate()`, `vsk.pushMatrix()`), randomness (`vsk.random()`, `vsk.randomGaussian()`, `vsk.noise()`), and more.

## Configs

Config files are JSON files in `art/<name>/config/`. When you run a sketch, if configs exist you'll be prompted to pick one (or skip). You can also pass one directly:

```bash
$ make run spiral
```

The framework applies the config values to the sketch's `Param` fields before drawing.

### GUI Parameter Editing with vsk

Each sketch is fully compatible with the `vsk` CLI. Run `vsk run art/<name>/generate.py` to open a live GUI where you can tweak `vsketch.Param` values interactively and see the result in real time. Save a configuration from there and place the resulting JSON in `art/<name>/config/` to use it with `make run`.

## Configuring the Plotter

Global plotter settings are at the top of `main.py`:

| Variable         | Default     | Description                                                                                             |
| ---------------- | ----------- | ------------------------------------------------------------------------------------------------------- |
| `HPGL_DEVICE`    | `"hp7475a"` | [vpype device](https://vpype.readthedocs.io/en/latest/reference.html#write) (controls units and limits) |
| `HPGL_PAGE_SIZE` | `"a4"`      | Paper size passed to vpype                                                                              |
| `HPGL_LANDSCAPE` | `True`      | Rotate output to landscape                                                                              |
| `HPGL_CENTER`    | `True`      | Center the drawing on the page                                                                          |
| `DRAW_SPEED`     | `40.0`      | Pen-down speed in mm/s (for preview timing)                                                             |
| `TRAVEL_SPEED`   | `200.0`     | Pen-up speed in mm/s (for preview timing)                                                               |

Page size and orientation are set per-sketch inside `draw()` via `vsk.size()`.

Supported `HPGL_DEVICE` values include: `hp7475a`, `hp7550`, `hp7440a`, `designmate`, `artisan`, `dmp_161`, `dxy`, `sketchmate`.

## Project Structure

```
art/              # one folder per sketch
  <name>/
    generate.py   # vsketch.SketchClass subclass — edit this
    config/       # optional JSON param configs
    renders/      # generated SVG and HPGL output
random/           # scratch / experimental scripts (not part of the pipeline)
models/           # shared 3D model data
utils/            # shared utilities (mesh, noise, wiggle)
hpgl_preview/     # HPGL parser and preview animation
sketch_template/  # cookiecutter template for new sketches
main.py           # CLI entry point
```

## Resources

- https://vsketch.readthedocs.io/en/latest/overview.html
- https://vpype.readthedocs.io/en/latest/
- https://paulbourke.net/dataformats/hpgl/
- https://cookiecutter.readthedocs.io/en/stable/
- https://github.com/abey79/cookiecutter-vsketch-sketch

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
