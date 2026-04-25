import os

import numpy as np
import vpype

MM_TO_PX = 96.0 / 25.4  # vpype uses CSS pixels (1 px = 1/96 inch)


def get_plottable_size(device, page_size, landscape):
    """
    Returns (width_mm, height_mm) of the actual plottable area for the given
    device/paper/orientation combo. Use this instead of raw paper dimensions
    to avoid geometry being clipped by vpype.
    """
    pc = vpype.config_manager.get_plotter_config(device)
    paper = pc.paper_config(page_size)
    unit_mm = pc.plotter_unit_length / MM_TO_PX
    x_mm = (paper.x_range[1] - paper.x_range[0]) * unit_mm
    y_mm = (paper.y_range[1] - paper.y_range[0]) * unit_mm
    # x_range is the long (landscape) axis, y_range is the short axis
    if landscape:
        return x_mm, y_mm
    else:
        return y_mm, x_mm


def prepare_vpype_document(width_mm, height_mm, polylines):
    lc = vpype.LineCollection()
    for polyline in polylines:
        if len(polyline) < 2:
            continue
        arr = np.array(
            [x * MM_TO_PX + 1j * y * MM_TO_PX for x, y in polyline],
            dtype=complex,
        )
        lc.append(arr)

    page_size_px = (width_mm * MM_TO_PX, height_mm * MM_TO_PX)

    return vpype.Document(lc, page_size=page_size_px)


def draw_svg(doc, art):
    output_folder = f"art/{art}/renders"
    os.makedirs(output_folder, exist_ok=True)

    svg_path = os.path.join(output_folder, f"{art}.svg")
    with open(svg_path, "w") as f:
        vpype.write_svg(f, doc, center=True)


def plot_hpgl(doc, art, page_size, landscape, center, device, velocity):
    output_folder = f"art/{art}/renders"
    os.makedirs(output_folder, exist_ok=True)

    hpgl_path = os.path.join(output_folder, f"{art}.hpgl")
    with open(hpgl_path, "w") as f:
        vpype.write_hpgl(
            f,
            doc,
            page_size,
            landscape,
            center,
            device,
            velocity,
            absolute=True,
        )
