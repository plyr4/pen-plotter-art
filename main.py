import argparse
import importlib

from plotter.conversion import draw_svg, plot_hpgl, prepare_vpype_document
from plotter.preview import preview_timeline


# page size in mm (A4 portrait)
WIDTH = 210
HEIGHT = 297

# plotter speeds in mm/s (used for animation timing)
DRAW_SPEED = 40.0   # mm/s, pen down
TRAVEL_SPEED = 200.0  # mm/s, pen up

# vpype device name used when writing HPGL (sets correct plotter units / paper limits)
# hp7475a, designmate, hp7440a, artisan, dmp_161, hp7550, dxy, sketchmate
HPGL_DEVICE = "hp7475a"
HPGL_PAGE_SIZE = "a4"
HPGL_LANDSCAPE = True
HPGL_CENTER = True
HPGL_VELOCITY = None

# python main.py --art spiral
if __name__ == "__main__":
    # load the given art
    parser = argparse.ArgumentParser()
    parser.add_argument("--art", default="spiral",
                        help="Name of the art piece to generate (folder name inside art/)")
    args = parser.parse_args()
    art_module = importlib.import_module(f"art.{args.art}.generate")

    # draw the art as "lines", a list of (x, y) pairs
    lines = art_module.generate_lines(WIDTH, HEIGHT)

    # convert lines to a vpype document (handles unit conversion and page size)
    vpype_doc = prepare_vpype_document(WIDTH, HEIGHT, lines)

    # draw the svg using the document
    draw_svg(vpype_doc, args.art)

    # draw the hpgl using the document
    plot_hpgl(vpype_doc, args.art, page_size=HPGL_PAGE_SIZE,
              landscape=HPGL_LANDSCAPE, center=HPGL_CENTER, device=HPGL_DEVICE, velocity=HPGL_VELOCITY)

    # show an animation of what the pen plotter will do with the hpgl file
    preview_timeline(DRAW_SPEED, TRAVEL_SPEED, args.art)
