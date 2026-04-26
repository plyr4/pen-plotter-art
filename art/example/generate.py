import vsketch
from shapely.geometry import LineString

MM_TO_PX = 96.0 / 25.4


class ExampleSketch(vsketch.SketchClass):
    page_size = vsketch.Param("a4")
    landscape = vsketch.Param(True)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size(self.page_size, landscape=self.landscape)
        vsk.scale("1mm")
        width = vsk.width / MM_TO_PX
        height = vsk.height / MM_TO_PX
        vsk.geometry(LineString([(0, 0), (width, height)]))
        vsk.geometry(LineString([(width, 0), (width, height)]))

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesort")


if __name__ == "__main__":
    ExampleSketch.display()
