import random

import vsketch
from shapely.geometry import LineString

from art.cube_shared import cube, wiggle_polyline

MM_TO_PX = 96.0 / 25.4


class CubeGuassSketch(vsketch.SketchClass):
    page_size = vsketch.Param("a4")
    landscape = vsketch.Param(True)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size(self.page_size, landscape=self.landscape)
        vsk.scale("1mm")
        width = vsk.width / MM_TO_PX
        height = vsk.height / MM_TO_PX

        lines = cube(width, height)
        amplitude = 0.5
        for line in lines:
            wiggled = wiggle_polyline(line, lambda mx, my: random.gauss(0, amplitude), segments=120)
            vsk.geometry(LineString(wiggled))

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesort")


if __name__ == "__main__":
    CubeGuassSketch.display()
