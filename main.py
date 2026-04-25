import argparse
import importlib
import os

from art_conversion.vpype import draw_svg, plot_hpgl, prepare_vpype_document
from hpgl_preview.timeline import show_timeline

# page size in mm (A4 portrait)
WIDTH = 210
HEIGHT = 297

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
    # load the given art
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

    # draw the art as "polylines", a list of (x, y) pairs
    polylines = art_module.generate_polylines(WIDTH, HEIGHT)

    # convert polylines to a vpype document (handles unit conversion and page size)
    vpype_doc = prepare_vpype_document(WIDTH, HEIGHT, polylines)

    # draw the svg using the document
    draw_svg(vpype_doc, args.art)

    # draw the hpgl using the document
    plot_hpgl(vpype_doc, args.art,
              HPGL_PAGE_SIZE, HPGL_LANDSCAPE,
              HPGL_CENTER, HPGL_DEVICE, HPGL_VELOCITY)

    # show an animation of what the pen plotter will do with the hpgl file
    show_timeline(DRAW_SPEED, TRAVEL_SPEED, args.art)
