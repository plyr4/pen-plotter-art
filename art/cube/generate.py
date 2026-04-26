import vsketch
from shapely.geometry import LineString

from art.cube_shared import cube

MM_TO_PX = 96.0 / 25.4


class CubeSketch(vsketch.SketchClass):
    page_size = vsketch.Param("a4")
    landscape = vsketch.Param(True)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size(self.page_size, landscape=self.landscape)
        vsk.scale("1mm")
        width = vsk.width / MM_TO_PX
        height = vsk.height / MM_TO_PX
        for polyline in cube(width, height):
            vsk.geometry(LineString(polyline))

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesort")


if __name__ == "__main__":
    CubeSketch.display()
