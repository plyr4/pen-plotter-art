import os

import vpype


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
