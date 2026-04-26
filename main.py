import argparse
import importlib
import inspect
import os

import vsketch

from art_conversion.vpype import draw_svg, plot_hpgl
from hpgl_preview.timeline import show_timeline

# vpype device name used when writing HPGL (sets correct plotter units / paper limits)
# hp7475a, designmate, hp7440a, artisan, dmp_161, hp7550, dxy, sketchmate
HPGL_DEVICE = "hp7475a"
HPGL_PAGE_SIZE = "a4"
HPGL_LANDSCAPE = True
HPGL_CENTER = True
HPGL_VELOCITY = None

# (used by the preview animation)
# plotter speeds in mm/s (used for animation timing)
DRAW_SPEED = 40.0   # mm/s, pen down
TRAVEL_SPEED = 200.0  # mm/s, pen up

# python main.py --art spiral
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--art", default="spiral",
                        help="Name of the art piece to generate (folder name inside art/)")
    args = parser.parse_args()

    try:
        art_module = importlib.import_module(f"art.{args.art}.generate")
    except ModuleNotFoundError:
        available = [d for d in os.listdir("art") if os.path.isdir(os.path.join("art", d)) and not d.startswith("_")]
        print(f"Error: art '{args.art}' not found. Available: {', '.join(sorted(available))}")
        raise SystemExit(1)

    # find the SketchClass subclass defined in this module
    sketch_cls = None
    for _name, obj in inspect.getmembers(art_module, inspect.isclass):
        if (issubclass(obj, vsketch.SketchClass)
                and obj is not vsketch.SketchClass
                and obj.__module__ == art_module.__name__):
            sketch_cls = obj
            break

    if sketch_cls is None:
        print(f"Error: no vsketch.SketchClass subclass found in art/{args.art}/generate.py")
        raise SystemExit(1)

    # execute the sketch (draw + finalize) to get the vpype document
    sketch = sketch_cls.execute(finalize=True)
    vpype_doc = sketch.vsk.document

    draw_svg(vpype_doc, args.art)
    plot_hpgl(vpype_doc, args.art,
              HPGL_PAGE_SIZE, HPGL_LANDSCAPE,
              HPGL_CENTER, HPGL_DEVICE, HPGL_VELOCITY)

    show_timeline(DRAW_SPEED, TRAVEL_SPEED, args.art)
