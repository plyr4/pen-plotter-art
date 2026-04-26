"""
Schotter — a recreation of Georg Nees' 1968 generative artwork.

A grid of squares that becomes increasingly rotated and displaced toward
the bottom of the page, transitioning from order to chaos.

Based on the vsketch README example: https://github.com/abey79/vsketch
"""

import vsketch

MM_TO_PX = 96.0 / 25.4

COLS = 12
ROWS = 22
CELL = 10  # mm per cell


class SchotterSketch(vsketch.SketchClass):
    page_size = vsketch.Param("a4")
    landscape = vsketch.Param(True)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size(self.page_size, landscape=self.landscape)
        vsk.scale("1mm")
        width = vsk.width / MM_TO_PX
        height = vsk.height / MM_TO_PX

        grid_w = COLS * CELL
        grid_h = ROWS * CELL
        vsk.translate((width - grid_w) / 2, (height - grid_h) / 2)

        for j in range(ROWS):
            fuzz = j / ROWS

            with vsk.pushMatrix():
                for i in range(COLS):
                    with vsk.pushMatrix():
                        vsk.rotate(fuzz * vsk.random(-25, 25), degrees=True)
                        vsk.translate(
                            fuzz * vsk.randomGaussian() * CELL * 0.15,
                            fuzz * vsk.randomGaussian() * CELL * 0.15,
                        )
                        vsk.rect(0, 0, CELL, CELL)
                    vsk.translate(CELL, 0)

            vsk.translate(0, CELL)

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesort")


if __name__ == "__main__":
    SchotterSketch.display()
