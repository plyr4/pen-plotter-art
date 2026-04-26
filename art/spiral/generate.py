import math

import vsketch
from shapely.geometry import LineString

MM_TO_PX = 96.0 / 25.4


class SpiralSketch(vsketch.SketchClass):
    page_size = vsketch.Param("a4")
    landscape = vsketch.Param(True)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size(self.page_size, landscape=self.landscape)
        vsk.scale("1mm")
        width = vsk.width / MM_TO_PX
        height = vsk.height / MM_TO_PX

        a = 0
        b = 1.3
        freq = 8.0
        step = 0.02
        amp = 10.0
        max_theta = 18 * math.pi
        cx, cy = width / 2, height / 2
        points, t = [], 0.0
        while t < max_theta:
            r = a + b * t + math.sin(t * freq) * amp
            points.append((cx + r * math.cos(t), cy + r * math.sin(t)))
            t += step
        vsk.geometry(LineString(points))

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesort")


if __name__ == "__main__":
    SpiralSketch.display()
