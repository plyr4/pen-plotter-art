import os

import numpy as np
import vpype

MM_TO_PX = 96.0 / 25.4  # vpype uses CSS pixels (1 px = 1/96 inch)


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
