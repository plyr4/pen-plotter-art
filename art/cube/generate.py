import math
import os
import sys
import vsketch
from shapely.geometry import LineString

# cross-compatibility with "vsk run" 
# fmt: off
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.mesh import project_mesh_occluded
from models.models import MODELS_PATH
# fmt: on


MM_TO_PX = 96.0 / 25.4
STL_PATH = os.path.join(MODELS_PATH, "cube", "cube.stl")


class CubeSketch(vsketch.SketchClass):
    page_size = vsketch.Param("a4")
    landscape = vsketch.Param(True)
    rot_x = vsketch.Param(25.0)  # degrees — tilt (tips top toward viewer)
    rot_z = vsketch.Param(45.0)  # degrees — spin around vertical axis

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size(self.page_size, landscape=self.landscape)
        vsk.scale("1mm")
        width = vsk.width / MM_TO_PX
        height = vsk.height / MM_TO_PX
        for polyline in project_mesh_occluded(
            STL_PATH, width, height,
            rot_x=math.radians(self.rot_x),
            rot_z=math.radians(self.rot_z),
            scale=1,
        ):
            vsk.geometry(LineString(polyline))
        # vsk.vpype("pixelize --pen-width .075mm")

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesort")


if __name__ == "__main__":
    CubeSketch.display()
