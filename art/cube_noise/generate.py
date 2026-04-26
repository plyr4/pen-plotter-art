import os

import numpy as np
import vsketch
from PIL import Image
from shapely.geometry import LineString

from art.cube_shared import cube, wiggle_polyline

MM_TO_PX = 96.0 / 25.4


def _load_noise():
    path = os.path.join(os.path.dirname(__file__), "noise2.png")
    img = Image.open(path).convert("L")
    arr = np.array(img, dtype=np.float32) / 255.0  # shape (H, W), values in [0, 1]
    return arr


def _sample_noise(arr, x, y, width, height):
    H, W = arr.shape
    ix = int((x / width) * W) % W
    iy = int((y / height) * H) % H
    return arr[iy, ix] * 2.0 - 1.0


class CubeNoiseSketch(vsketch.SketchClass):
    page_size = vsketch.Param("a4")
    landscape = vsketch.Param(True)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size(self.page_size, landscape=self.landscape)
        vsk.scale("1mm")
        width = vsk.width / MM_TO_PX
        height = vsk.height / MM_TO_PX

        noise = _load_noise()
        amplitude = 2.5
        lines = cube(width, height)
        for line in lines:
            wiggled = wiggle_polyline(
                line,
                lambda mx, my: _sample_noise(noise, mx, my, width, height) * amplitude,
                segments=400,
            )
            vsk.geometry(LineString(wiggled))

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesort")


if __name__ == "__main__":
    CubeNoiseSketch.display()
